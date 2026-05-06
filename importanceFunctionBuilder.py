import copy, logging, math, psutil, time
from typing import Callable, List, Literal as TypingLiteral, Sequence
from collections import deque
from pympler import asizeof
from DMB import DBM
from models.stateSnapshot import StateSnapShot
from models.STA import *
from models.stateClass import StateClass

logger = logging.getLogger(__name__)

SupportKind = TypingLiteral["finite", "lower-bounded", "upper-bounded", "unbounded", "unknown"]
SupportInfo = tuple[float | None, float | None, SupportKind]


class ImportanceFunctionBuilder:
    def __init__(
        self,
        automaton: Automaton,
        rareEventLocationName: str,
        mbLimit: int,
        modelsVariables: Sequence[Variable] | None,
        exponentialTruncationEpsilon: float | None = None,
        timeLimitSeconds: float | None = None,
    ):
        """Initialize builder state and precompute hop/time distance dictionaries."""
        self.automaton = automaton
        self.modelsVariables = modelsVariables
        rareEventLocation = self.automaton.getLocationByName(rareEventLocationName)
        if rareEventLocation is None:
            raise ValueError(f"Rare event location '{rareEventLocationName}' not found in automaton.")
        self.rareEventLocation = rareEventLocation
        self.mbLimit = mbLimit
        self.timeLimitSeconds = timeLimitSeconds
        self._constantValues: dict[str, float] = {}
        if exponentialTruncationEpsilon is not None and not (0.0 < exponentialTruncationEpsilon < 1.0):
            raise ValueError("exponentialTruncationEpsilon must be in the open interval (0, 1).")
        self._exponentialTruncationEpsilon = exponentialTruncationEpsilon
        self._projectionWarningKeys: set[tuple[str, str, str | None]] = set()
        self._knownVariableNames = self._collectKnownVariableNames()
        self._edgeDistributionSupports = self._buildEdgeDistributionSupports()
        self._locationDistributionSupports = self._buildLocationDistributionSupports()
        self._distributionSupports = self._buildDistributionSupports()
        self.clocks = self._identifyRelevantClocks()
        self.hopDistanceDict = self._hopDistanceDictBuilder()
        self.timeDistanceDict = self._timeDistanceDictBuilder()

        self.hopDistanceDict = {
            location: distance
            for location, distance in self.hopDistanceDict.items()
            if location not in self.timeDistanceDict
        }

    @staticmethod
    def _supportBounds(kind: SupportKind, low: float | None, high: float | None) -> tuple[float | None, float | None]:
        """Normalize support kind to explicit lower/upper bound presence."""
        if kind == "finite":
            if low is None or high is None:
                return (None, None)
            return (low, high)
        if kind == "lower-bounded":
            return (low, None)
        if kind == "upper-bounded":
            return (None, high)
        return (None, None)

    @staticmethod
    def _kindFromBounds(low: float | None, high: float | None) -> SupportKind:
        """Infer support kind from bound availability."""
        if low is None and high is None:
            return "unbounded"
        if low is not None and high is not None:
            return "finite"
        if low is not None:
            return "lower-bounded"
        return "upper-bounded"

    def _warnProjectionIssueOnce(
        self,
        warningKind: str,
        variableName: str,
        contextLocation: str | None,
        message: str,
        *args: object,
    ) -> None:
        """Log projection warnings once per variable/location to reduce log noise."""
        key = (warningKind, variableName, contextLocation)
        if key in self._projectionWarningKeys:
            return
        self._projectionWarningKeys.add(key)
        logger.warning(message, *args)

    def _buildEdgeDistributionSupports(self) -> dict[Edge, dict[str, SupportInfo]]:
        """Infer support metadata per edge for sampled variables assigned on that edge."""
        supportsByEdge: dict[Edge, dict[str, SupportInfo]] = {}

        for edge in self.automaton.edges:
            scoped: dict[str, SupportInfo] = {}
            for destination in edge.destinations:
                for assignment in destination.assignments:
                    if isinstance(assignment.value, Distribution):
                        self._mergeSupport(scoped, assignment.ref, self._supportFromDistribution(assignment.value))
            if scoped:
                supportsByEdge[edge] = scoped

        return supportsByEdge

    def _buildLocationDistributionSupports(self) -> dict[str, dict[str, SupportInfo]]:
        """Infer support metadata per active location for sampled variables.

        Location-scoped support is more precise than global support. It is built from:
        - variable initial distributions on initial locations
        - distribution assignments on transition destinations
        """
        supportsByLocation: dict[str, dict[str, SupportInfo]] = {}

        for variable in self.automaton.variables:
            initial = variable.initial_value
            if not isinstance(initial, Distribution):
                continue
            incoming = self._supportFromDistribution(initial)
            for initialLocation in self.automaton.initial_locations:
                scoped = supportsByLocation.setdefault(initialLocation, {})
                self._mergeSupport(scoped, variable.name, incoming)

        for edge in self.automaton.edges:
            for destination in edge.destinations:
                scoped = supportsByLocation.setdefault(destination.location, {})
                for assignment in destination.assignments:
                    if isinstance(assignment.value, Distribution):
                        self._mergeSupport(scoped, assignment.ref, self._supportFromDistribution(assignment.value))

        return supportsByLocation

    def _collectKnownVariableNames(self) -> set[str]:
        """Collect all model/automaton variable names treated as non-constant symbols in guards."""
        names = {variable.name for variable in self.automaton.variables}
        if self.modelsVariables is not None:
            names.update(variable.name for variable in self.modelsVariables)
        return names

    def _buildDistributionSupports(self) -> dict[str, SupportInfo]:
        """Infer support metadata for sampled variables from initial values and assignments.

        Returns mapping variable -> (lower, upper, kind), where kind is one of
        "finite", "lower-bounded", "upper-bounded", "unbounded", or "unknown".
        """
        supports: dict[str, SupportInfo] = {}

        for variable in self.automaton.variables:
            initial = variable.initial_value
            if isinstance(initial, Distribution):
                self._mergeSupport(supports, variable.name, self._supportFromDistribution(initial))

        for edge in self.automaton.edges:
            for destination in edge.destinations:
                for assignment in destination.assignments:
                    if isinstance(assignment.value, Distribution):
                        self._mergeSupport(supports, assignment.ref, self._supportFromDistribution(assignment.value))

        return supports

    @staticmethod
    def _mergeSupport(
        supports: dict[str, SupportInfo],
        variableName: str,
        incoming: SupportInfo,
    ) -> None:
        """Merge support info for the same variable across multiple sampling sites.

        If any site is unknown/unbounded, merged support remains conservative.
        """
        current = supports.get(variableName)
        if current is None:
            supports[variableName] = incoming
            return

        curLow, curHigh, curKind = current
        inLow, inHigh, inKind = incoming

        if curKind == "unknown" or inKind == "unknown":
            supports[variableName] = (None, None, "unknown")
            return

        curLowBound, curHighBound = ImportanceFunctionBuilder._supportBounds(curKind, curLow, curHigh)
        inLowBound, inHighBound = ImportanceFunctionBuilder._supportBounds(inKind, inLow, inHigh)

        mergedLow = None if curLowBound is None or inLowBound is None else min(curLowBound, inLowBound)
        mergedHigh = None if curHighBound is None or inHighBound is None else max(curHighBound, inHighBound)
        mergedKind = ImportanceFunctionBuilder._kindFromBounds(mergedLow, mergedHigh)
        supports[variableName] = (mergedLow, mergedHigh, mergedKind)

    def _supportFromDistribution(self, distribution: Distribution) -> SupportInfo:
        """Translate a distribution declaration into support metadata.

        Current policy:
        - Uniform(a,b): finite support [min(a,b), max(a,b)] when numeric
        - Exponential: lower-bounded support [0, +inf), optionally truncated
          to finite support via epsilon-tail mode.
        - Normal: unbounded support
        - Other/unevaluable distributions: unknown support
        """
        distributionType = distribution.type.casefold()

        if distributionType == "uniform":
            if len(distribution.args) != 2:
                return (None, None, "unknown")
            lower = self._tryEvaluateNumericExpression(distribution.args[0])
            upper = self._tryEvaluateNumericExpression(distribution.args[1])
            if lower is None or upper is None:
                return (None, None, "unknown")
            return (min(lower, upper), max(lower, upper), "finite")

        if distributionType == "exponential":
            lowerBound = 0.0

            if self._exponentialTruncationEpsilon is None:
                return (lowerBound, None, "lower-bounded")

            if len(distribution.args) != 1:
                return (lowerBound, None, "lower-bounded")

            rate = self._tryEvaluateNumericExpression(distribution.args[0])
            if rate is None or rate <= 0:
                return (lowerBound, None, "lower-bounded")

            upperBound = -math.log(self._exponentialTruncationEpsilon) / rate
            return (lowerBound, upperBound, "finite")

        if distributionType == "normal":
            return (None, None, "unbounded")

        return (None, None, "unknown")

    def _tryEvaluateNumericExpression(self, expression: Expression) -> float | None:
        """Try to evaluate arithmetic expressions to a numeric constant.

        This is used for distribution parameters and constants. Returns None when
        evaluation depends on unresolved symbols.
        """
        if isinstance(expression, Literal):
            value = expression.value
            if isinstance(value, bool):
                return None
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    return float(value)
                except ValueError:
                    return None
            return None

        if isinstance(expression, VariableReference):
            if expression.name in self._constantValues:
                return self._constantValues[expression.name]
            return None

        if isinstance(expression, UnaryExpression):
            inner = self._tryEvaluateNumericExpression(expression.exp)
            if inner is None:
                return None
            if expression.op == "+":
                return inner
            if expression.op == "-":
                return -inner
            return None

        if isinstance(expression, BinaryExpression):
            left = self._tryEvaluateNumericExpression(expression.left)
            right = self._tryEvaluateNumericExpression(expression.right)
            if left is None or right is None:
                return None
            if expression.op == "+":
                return left + right
            if expression.op == "-":
                return left - right
            if expression.op == "*":
                return left * right
            if expression.op == "/":
                if right == 0:
                    return None
                return left / right
            return None

        return None

    def _negateExpression(self, expression: Expression) -> Expression:
        """Push logical negation into a guard expression where possible.

        Applies De Morgan for conjunction/disjunction and flips comparison
        operators. Falls back to wrapping in a UnaryExpression for unsupported types.
        """
        if isinstance(expression, UnaryExpression) and expression.op == "¬":
            return expression.exp

        if isinstance(expression, BinaryExpression):
            if expression.op == "∧":
                return BinaryExpression("∨", self._negateExpression(expression.left), self._negateExpression(expression.right))
            if expression.op == "∨":
                return BinaryExpression("∧", self._negateExpression(expression.left), self._negateExpression(expression.right))

            comparatorNegations = {
                "<": ">=",
                "<=": ">",
                "≤": ">",
                ">": "<=",
                ">=": "<",
                "≥": "<",
            }
            if expression.op in comparatorNegations:
                return BinaryExpression(comparatorNegations[expression.op], expression.left, expression.right)

        # Fallback for expressions that cannot be structurally negated (e.g. VariableReference)
        return UnaryExpression("¬", expression)

    def _toAffine(self, expression: Expression) -> tuple[dict[str, float], float, set[str]]:
        """Normalize arithmetic expression into affine form.

        Returns (coefficients, constant, unresolved_constants) where:
        - coefficients maps variable name -> coefficient
        - constant is the numeric free term
        - unresolved_constants are symbol names not known as variables and not
          resolved at runtime
        """
        if isinstance(expression, Literal):
            value = expression.value
            if isinstance(value, bool):
                raise ValueError("Boolean literals are not valid in arithmetic guard expressions.")
            if isinstance(value, (int, float)):
                return ({}, float(value), set())
            if isinstance(value, str):
                try:
                    return ({}, float(value), set())
                except ValueError:
                    raise ValueError(f"Unsupported literal in arithmetic guard expression: {value}")
            raise ValueError(f"Unsupported literal in arithmetic guard expression: {value}")

        if isinstance(expression, VariableReference):
            if expression.name in self._knownVariableNames:
                return ({expression.name: 1.0}, 0.0, set())
            if expression.name in self._constantValues:
                return ({}, self._constantValues[expression.name], set())
            return ({}, 0.0, {expression.name})

        if isinstance(expression, UnaryExpression):
            coeffs, constant, unresolved = self._toAffine(expression.exp)
            if expression.op == "+":
                return (coeffs, constant, unresolved)
            if expression.op == "-":
                return ({name: -value for name, value in coeffs.items()}, -constant, set(unresolved))
            raise ValueError(f"Unsupported unary arithmetic operation in guard expression: {expression.op}")

        if isinstance(expression, BinaryExpression):
            leftCoeffs, leftConstant, leftUnresolved = self._toAffine(expression.left)
            rightCoeffs, rightConstant, rightUnresolved = self._toAffine(expression.right)

            if expression.op == "+":
                combinedCoeffs = dict(leftCoeffs)
                for name, value in rightCoeffs.items():
                    combinedCoeffs[name] = combinedCoeffs.get(name, 0.0) + value
                return (combinedCoeffs, leftConstant + rightConstant, leftUnresolved | rightUnresolved)

            if expression.op == "-":
                combinedCoeffs = dict(leftCoeffs)
                for name, value in rightCoeffs.items():
                    combinedCoeffs[name] = combinedCoeffs.get(name, 0.0) - value
                return (combinedCoeffs, leftConstant - rightConstant, leftUnresolved | rightUnresolved)

            raise ValueError(f"Unsupported arithmetic operation in guard expression: {expression.op}")

        raise ValueError(f"Unsupported arithmetic expression type: {type(expression).__name__}")

    def _getDistributionSupportForVariable(
        self,
        variableName: str,
        contextLocation: str | None,
        contextEdge: Edge | None,
    ) -> SupportInfo | None:
        """Get support metadata for a sampled variable.

        Resolution order:
        1. Edge-scoped support when edge context is available
        2. Location-scoped support when context location is available
        3. Global merged support fallback
        """
        if contextEdge is not None:
            edgeScoped = self._edgeDistributionSupports.get(contextEdge)
            if edgeScoped is not None and variableName in edgeScoped:
                return edgeScoped[variableName]

        if contextLocation is not None:
            scoped = self._locationDistributionSupports.get(contextLocation)
            if scoped is not None and variableName in scoped:
                return scoped[variableName]
        return self._distributionSupports.get(variableName)

    def build(self) -> Callable[[StateSnapShot], int]:
        """Return the callable importance function for state snapshots."""
        return self._importanceFunction

    def getClocksNames(self) -> List[str]:
        return self.clocks

    def _importanceFunction(self, snapShot: StateSnapShot) -> int:
        """Compute the importance score for a snapshot using time-distance then hop-distance fallback."""
        # Check for time distance score first
        locationName = snapShot.locationName
        stateClasses = self.timeDistanceDict.get(locationName)

        if stateClasses:
            holdingStateClasses = [stateClass for stateClass in stateClasses
                                   if stateClass.dmb is not None and
                                   stateClass.dmb.isSatisfiedBy(snapShot.clocks)]
            if holdingStateClasses:
                bestStateClass = min(holdingStateClasses, key=lambda sc: sc.distance)
                return bestStateClass.distance
             # No time-distance class applies, return a large number to indicate low importance
            return int(1e9)
        #print(f"No time-distance classes found for location '{locationName}'. Falling back to hop distance.")
        hopDistance = self.hopDistanceDict.get(locationName)
        if hopDistance is None:
            raise KeyError(f"Location {locationName} not found in hop distance dictionary.")
        return hopDistance

    def _hopDistanceDictBuilder(self) -> dict[str, int]:
        """Build reverse-BFS hop distances from every location to the rare event location."""

        visitedSet = set()
        toVisitQueue: deque[StateClass] = deque()
        hopDistanceDict: dict[str, int] = {}
        rareEventStateScore = StateClass(self.rareEventLocation.name, None, 0)

        toVisitQueue.append(rareEventStateScore)

        while toVisitQueue:
            current: StateClass = toVisitQueue.popleft()

            visitedSet.add(current.locationName)
            hopDistanceDict[current.locationName] = current.distance

            # Add locations that have an edge going to current
            for edge in self.automaton.edges:
                if edge.location in visitedSet:
                    continue

                if any(destination.location == current.locationName
                       for destination in edge.destinations):
                    toVisitQueue.append(
                        StateClass(edge.location, None, current.distance + 1))

        return hopDistanceDict

    def _timeDistanceDictBuilder(self) -> dict[str, List[StateClass]]:
        """Perform backward analysis and build DMB-based distance classes per location."""
        statesToProcess: deque[StateClass] = deque()

        targetStateClass = StateClass(self.rareEventLocation.name, DBM(self.clocks), 0)
        statesToProcess.append(targetStateClass)

        visitedDict: dict[str, List[StateClass]] = {targetStateClass.locationName: [targetStateClass]}
        iteration = 0
        startTime = time.perf_counter()

        estimateSizeMb = asizeof.asizeof(targetStateClass) / (1024 * 1024)
        print(f"Estimated size per state class: {estimateSizeMb:.4f} MB")
        while statesToProcess:
            iteration += 1
            interval = self._progressInterval(iteration)
            if iteration % interval == 0:
                print(
                    f"Memory used: {self._getMemoryUsageMb():.2f} MB, "
                    f"Queue size: {len(statesToProcess)}, Locations with DBMs: {len(visitedDict)}, "
                    f"Iteration: {iteration}"
                )

            if self.timeLimitSeconds is not None:
                if time.perf_counter() - startTime > self.timeLimitSeconds:
                    logger.warning(f"Time limit of {self.timeLimitSeconds} seconds reached. Stopping backward analysis.")
                    return visitedDict

            current: StateClass = statesToProcess.popleft()

            # Find incoming edges to current location
            location = self.automaton.getLocationByName(current.locationName)
            if location is None:
                raise ValueError(f"Location {current.locationName} not found in automaton.")
            incomingEdges = self.automaton.getIncomingEdges(location)

            if self.mbLimit is not None:
                # Check if adding these will exceed the limit
                # We use a safety buffer (e.g., 0.95) to allow for the objects in visitedDict too
                if self._getMemoryUsageMb() + (len(incomingEdges) * estimateSizeMb) > self.mbLimit * 1.0:
                    logger.warning("Memory limit approaching. Stopping backward analysis.")
                    return visitedDict

            # For each incoming edge, calculate the new DMB and distance metric for the source location
            for edge in incomingEdges:
                incomingDMB = copy.deepcopy(current.dmb)
                if incomingDMB is None:
                    raise ValueError("DMB should not be None.")

                # Check for a clock reset and update the DMB accordingly
                self._applyClockResets(incomingDMB, edge, current)

                # Apply the guards of the edge to update the DMB
                incomingDMBs = self._applyConstraintExpressionToDMB(
                    edge.guard,
                    [incomingDMB],
                    contextLocation=edge.location,
                    contextEdge=edge,
                )

                # Apply source location invariant to the DMB
                sourceLocation = self.automaton.getLocationByName(edge.location)
                if sourceLocation is None:
                    raise ValueError(f"Source location {edge.location} not found in automaton.")
                incomingDMBs = self._applyConstraintExpressionToDMB(
                    sourceLocation.timeProgress,
                    incomingDMBs,
                    contextLocation=sourceLocation.name,
                    contextEdge=edge,
                )

                # Normilize the DMB
                validDMBs: List[DBM] = []
                for dmb in incomingDMBs:
                    dmb.normalize()

                    if dmb.isEmpty():
                        continue

                    dmb.removeLowerBounds()

                    dmb.normalize()

                    validDMBs.append(dmb)

                # Construct new stateClasses
                incommingStateClasses = [
                    StateClass(edge.location, dmb, current.distance + 1)
                    for dmb in validDMBs]
                incommingStateClasses = self._mergeStateClasses([], incommingStateClasses)

                # Check if we have already visited the source location with a DMB
                stateClasses = visitedDict.get(edge.location, None)
                if stateClasses is None:
                    visitedDict[edge.location] = incommingStateClasses
                    statesToProcess.extend(incommingStateClasses)
                else:
                    mergedStateClasses = self._mergeStateClasses(stateClasses, incommingStateClasses)
                    if mergedStateClasses != stateClasses:
                        visitedDict[edge.location] = mergedStateClasses
                        contributingStateClasses = [
                            stateClass
                            for stateClass in incommingStateClasses
                            if stateClass in mergedStateClasses and stateClass not in stateClasses
                        ]
                        if contributingStateClasses:
                            statesToProcess.extend(contributingStateClasses)

        return visitedDict

    @staticmethod
    def _progressInterval(iteration: int) -> int:
        """Determine logging interval based on iteration count to balance feedback and overhead."""
        if iteration <= 10:
            return 1
        if iteration <= 110:
            return 10
        if iteration <= 1110:
            return 100
        return 1000

    def _getMemoryUsageMb(self) -> float:
        """Get current memory usage in mb."""
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)

    def _identifyRelevantClocks(self) -> List[str]:
        """Extract clocks and accumulators from the automation variables"""
        # Get clocks
        clockNames = [variable.name for variable in self.automaton.variables if variable.type == "clock"]

        # Remove local sojourn clock
        """
        appearances[c] = {
            reset on:    set of edges where c is assigned 0,
            guarded on:  set of locations where c appears in outgoing guards,
            invariant on: set of locations where c appears in time-progress
        }
        """

        appearances: dict[str, tuple[set[Edge], set[str], set[str]]] = {}

        def addToAppearances(name: str, index: int, value: Edge | str) -> None:
            if name not in clockNames:
                return

            if name not in appearances:
                appearances[name] = (set(), set(), set())

            if index == 0:
                if not isinstance(value, Edge):
                    raise ValueError("Expected Edge for index zero.")
                appearances[name][0].add(value)
            elif index == 1:
                if not isinstance(value, str):
                    raise ValueError("Expected location name for index one.")
                appearances[name][1].add(value)
            elif index == 2:
                if not isinstance(value, str):
                    raise ValueError("Expected location name for index two.")
                appearances[name][2].add(value)
            else:
                raise ValueError(f"Unsupported index: {index}")

        for edge in self.automaton.edges:
            for destination in edge.destinations:
                # Reset on
                for name in self._findNamesAssignedZero(destination.assignments):
                    addToAppearances(name, 0, edge)

            # Guarded on (source location of the edge)
            if isinstance(edge.guard, Expression):
                for name in self._findVariableReferenceNames(edge.guard):
                    addToAppearances(name, 1, edge.location)

        # Invariant on
        for location in self.automaton.locations:
            if isinstance(location.timeProgress, Expression):
                for name in self._findVariableReferenceNames(location.timeProgress):
                    addToAppearances(name, 2, location.name)

        # Prune clocks
        nonLocalClockNames = []
        for clockName in clockNames:
            apperance = appearances.get(clockName, None)
            if apperance is None:
                logger.warning(f"Clock '{clockName}' is not used in any guard, invariant, or reset. It will be ignored in the importance function.")
                continue
            resetOn, guardedOn, invariantOn = apperance
            # appers in more than one location guard or invariant hence not a local sojourn clock
            if len(guardedOn) != 1 or len(invariantOn) != 1:
                nonLocalClockNames.append(clockName)
                continue
            # appears in different locations' guards and invariants hence not a local sojourn clock
            if  guardedOn != invariantOn:
                nonLocalClockNames.append(clockName)
                continue
            # appears in the guard of an edge that does not reset it, hence not a local sojourn clock
            guardedLocationName = next(iter(guardedOn))
            location = self.automaton.getLocationByName(guardedLocationName)
            if location is None:
                raise ValueError(f"Location {guardedLocationName} not found in automaton.")

            if not all(edge in resetOn for edge in self.automaton.getIncomingEdges(location)):
                nonLocalClockNames.append(clockName)
                continue
            logger.info(f"Clock '{clockName}' is identified as a local sojourn clock for location '{location.name}' and will be ignored in the importance function.")

        print(f"Identified non-local clocks: {nonLocalClockNames}")

        accumulatorNamesAutomata = [variable.name for variable in self.automaton.variables if variable.accumulator]
        print(f"Identified accumulator names in automata: {accumulatorNamesAutomata}")

        if self.modelsVariables is not None:
            accumulatorNammesModel = [variable.name for variable in self.modelsVariables if variable.accumulator]
            print(f"Identified accumulator names in models: {accumulatorNammesModel}")

            return nonLocalClockNames + accumulatorNamesAutomata + accumulatorNammesModel

        return nonLocalClockNames + accumulatorNamesAutomata

    def _findVariableReferenceNames(self, expression: Expression) -> set[str]:
        names: set[str] = set()

        def visit(node: Expression) -> None:
            if isinstance(node, VariableReference):
                names.add(node.name)
            elif isinstance(node, Literal):
                return
            elif isinstance(node, BinaryExpression):
                visit(node.left)
                visit(node.right)
            elif isinstance(node, IfThenElse):
                visit(node.condition)
                visit(node.then)
                visit(node.else_)
            elif isinstance(node, UnaryExpression):
                visit(node.exp)
            else:
                raise TypeError(f"Unsupported expression type: {type(node).__name__}")

        visit(expression)
        return names

    def _findNamesAssignedZero(self, assignments: Sequence[Assignment]) -> list[str]:
        names: list[str] = []

        for assignment in assignments:
            value = assignment.value
            if isinstance(value, Distribution):
                continue
            if self._expressionContainsAssignedZero(value):
                names.append(assignment.ref)

        return names

    @staticmethod
    def _expressionContainsAssignedZero(expr: Expression) -> bool:
        def is_zero_literal(node: Expression) -> bool:
            if not isinstance(node, Literal):
                return False

            v = node.value
            if isinstance(v, (int, float)):
                return v == 0
            if isinstance(v, str):
                try:
                    return float(v) == 0.0
                except ValueError:
                    return False
            return False

        if is_zero_literal(expr):
            return True

        if isinstance(expr, Literal):
            return False

        if isinstance(expr, VariableReference):
            return False

        if isinstance(expr, UnaryExpression):
            return ImportanceFunctionBuilder._expressionContainsAssignedZero(expr.exp)

        if isinstance(expr, BinaryExpression):
            # Visit both sides of the value expression.
            return (
                ImportanceFunctionBuilder._expressionContainsAssignedZero(expr.left)
                or ImportanceFunctionBuilder._expressionContainsAssignedZero(expr.right)
            )

        if isinstance(expr, IfThenElse):
            # "Makes sense" for assignment value: then/else branches.
            return (
                ImportanceFunctionBuilder._expressionContainsAssignedZero(expr.then)
                or ImportanceFunctionBuilder._expressionContainsAssignedZero(expr.else_)
            )

        raise TypeError(f"Unsupported expression type: {type(expr).__name__}")

    def _applyClockResets(self, dmb: DBM, edge: Edge, current: StateClass) -> None:
        """
        Apply clock resets on the transition into the current location by freeing reset clocks.
        """
        for destination in edge.destinations:
            if destination.location == current.locationName:
                zeroNames = self._findNamesAssignedZero(destination.assignments)
                for zeroName in zeroNames:
                    if zeroName in dmb.clocks:
                        dmb.removeConstrains(zeroName)

    @staticmethod
    def _mergeStateClasses(existing: List[StateClass], incoming: List[StateClass]) -> List[StateClass]:
        """
        Merging is done by checking for dominance between the DMBs of the state classes.\n
        We say that state class A dominates state class B if the DMB of A is a subset
        of the DMB of B and the distance metric of A is less than or equal to that of B.
        In this case, B can be removed from the merged list as A provides at least
        as much information with a better or equal distance metric.\n
        Symmetric dominance is also checked: if the DMB of the incoming state class
        is a subset of an existing state class and has a distance metric that is
        greater than or equal to the existing one, then the incoming state class can be
        skipped as it provides no additional information.\n
        All remaining state classes that are not dominated or
        symmetrically dominated are kept in the merged list.
        """
        merged = list(existing)

        for stateClassNew in incoming:
            dmbNew = stateClassNew.dmb
            if dmbNew is None:
                raise ValueError("DMB should not be None.")

            skipNew = False
            updatedExisting: List[StateClass] = []
            for stateClassOld in merged:
                dmbOld = stateClassOld.dmb
                if dmbOld is None:
                    raise ValueError("DMB should not be None.")

                # D1 subset D2 and d1 >= d2: keep Sigma2
                if dmbOld.isSubset(dmbNew) and stateClassOld.distance >= stateClassNew.distance:
                    continue

                # Symmetric dominance: if new is contained in old and has no better distance,
                # it brings no additional information.
                if dmbNew.isSubset(dmbOld) and stateClassNew.distance >= stateClassOld.distance:
                    skipNew = True

                # All remaining cases in the current design keep old and new.
                updatedExisting.append(stateClassOld)

            if not skipNew:
                updatedExisting.append(stateClassNew)
            merged = updatedExisting

        return merged

    @staticmethod
    def _dedupeDMBs(dmbs: List[DBM]) -> List[DBM]:
        """Remove duplicate DMBs while preserving the first occurrence order."""
        uniqueDMBs: List[DBM] = []
        for dmb in dmbs:
            if any(dmb == existing for existing in uniqueDMBs):
                continue
            uniqueDMBs.append(dmb)
        return uniqueDMBs

    def _applyComparisonConstraint(
        self,
        dmb: DBM,
        left: Expression,
        right: Expression,
        op: str,
        contextLocation: str | None,
        contextEdge: Edge | None,
    ) -> None:
        """Apply one comparison guard by projecting it onto DMB-supported constraints.

        Workflow:
        1. Normalize comparison to affine <= form.
        2. Require runtime-resolved constants when tracked variables are involved.
        3. Eliminate untracked sampled variables using finite support projection.
        4. Emit DMB constraints only for difference-constraint-compatible forms.
        """
        if op in {"<", ">"}:
            ""
            #logger.warning("Approximating strict inequality '%s' as non-strict bounds in DMB.", op)

        match op:
            case "<" | "<=" | "≤":
                leftCoeffs, leftConstant, leftUnresolved = self._toAffine(left)
                rightCoeffs, rightConstant, rightUnresolved = self._toAffine(right)
                coeffs = dict(leftCoeffs)
                for name, value in rightCoeffs.items():
                    coeffs[name] = coeffs.get(name, 0.0) - value
                constant = leftConstant - rightConstant
                unresolvedSymbols = leftUnresolved | rightUnresolved
            case ">" | ">=" | "≥":
                leftCoeffs, leftConstant, leftUnresolved = self._toAffine(right)
                rightCoeffs, rightConstant, rightUnresolved = self._toAffine(left)
                coeffs = dict(leftCoeffs)
                for name, value in rightCoeffs.items():
                    coeffs[name] = coeffs.get(name, 0.0) - value
                constant = leftConstant - rightConstant
                unresolvedSymbols = leftUnresolved | rightUnresolved
            case _:
                raise ValueError(f"Unsupported comparison operator: {op}")

        coefficients = {
            name: value
            for name, value in coeffs.items()
            if abs(value) > 1e-12
        }

        trackedVariables = {name for name in coefficients if name in dmb.clocks}
        if unresolvedSymbols and trackedVariables:
            unresolved = ", ".join(sorted(unresolvedSymbols))
            raise ValueError(
                f"Missing runtime value for constant(s): {unresolved}. "
                f"These constants are required for constraints over tracked variables: {sorted(trackedVariables)}"
            )

        if not trackedVariables:
            return

        # Eliminate untracked terms by existential projection where finite support is known.
        for name in list(coefficients.keys()):
            coefficient = coefficients[name]
            if name in dmb.clocks:
                continue

            support = self._getDistributionSupportForVariable(name, contextLocation, contextEdge)
            if support is None:
                self._warnProjectionIssueOnce(
                    "missing-support",
                    name,
                    contextLocation,
                    "Skipping guard comparison term for untracked variable '%s' without distribution support metadata (location=%s, edge=%s).",
                    name,
                    contextLocation,
                    contextEdge,
                )
                return

            low, high, supportKind = support
            if coefficient >= 0:
                if low is None:
                    self._warnProjectionIssueOnce(
                        "missing-lower-bound",
                        name,
                        contextLocation,
                        "Skipping one-sided projection for untracked sampled variable '%s' with support kind '%s'; missing lower bound (location=%s, edge=%s).",
                        name,
                        supportKind,
                        contextLocation,
                        contextEdge,
                    )
                    return
                chosen = low
            else:
                if high is None:
                    self._warnProjectionIssueOnce(
                        "missing-upper-bound",
                        name,
                        contextLocation,
                        "Skipping one-sided projection for untracked sampled variable '%s' with support kind '%s'; missing upper bound (location=%s, edge=%s).",
                        name,
                        supportKind,
                        contextLocation,
                        contextEdge,
                    )
                    return
                chosen = high

            constant += coefficient * chosen
            del coefficients[name]

        coefficients = {
            name: value
            for name, value in coefficients.items()
            if abs(value) > 1e-12
        }

        if len(coefficients) == 0:
            if constant > 0:
                dmb.addConstraint("0", "0", -1)
            return

        if len(coefficients) == 1:
            (name, coefficient), = coefficients.items()
            if name not in dmb.clocks:
                return
            if abs(coefficient - 1.0) < 1e-12:
                dmb.addConstraint(name, "0", -constant)
                return
            if abs(coefficient + 1.0) < 1e-12:
                dmb.addConstraint("0", name, constant)
                return
            raise ValueError(
                f"Unsupported non-unit coefficient '{coefficient}' for tracked variable '{name}' in guard comparison."
            )

        if len(coefficients) == 2:
            items = list(coefficients.items())
            (nameA, coefficientA), (nameB, coefficientB) = items
            if nameA not in dmb.clocks or nameB not in dmb.clocks:
                logger.warning(
                    "Skipping comparison with mixed tracked/untracked two-variable form after projection: %s",
                    coefficients,
                )
                return

            if abs(coefficientA - 1.0) < 1e-12 and abs(coefficientB + 1.0) < 1e-12:
                dmb.addConstraint(nameA, nameB, -constant)
                return
            if abs(coefficientA + 1.0) < 1e-12 and abs(coefficientB - 1.0) < 1e-12:
                dmb.addConstraint(nameB, nameA, -constant)
                return

            raise ValueError(
                "Unsupported two-variable affine guard; DMB requires difference constraints of the form x - y <= c. "
                f"Received coefficients: {coefficients}"
            )

        raise ValueError(
            "Unsupported affine guard over more than two tracked variables; "
            "DMB supports only difference constraints x - y <= c."
        )

    def _applyConstraintExpressionToDMB(
        self,
        guard: Expression | None,
        dmbs: List[DBM],
        contextLocation: str | None = None,
        contextEdge: Edge | None = None,
    ) -> List[DBM]:
        """Apply a full guard expression to one or more DMB branches.

        Supports:
        - conjunction via sequential refinement
        - disjunction via branch splitting
        - comparisons via affine projection
        - unary negation via normalization

        Over-approximates by ignoring expressions that do not constrain clocks.
        """
        if guard is None:
            return dmbs

        if isinstance(guard, Literal):
            if isinstance(guard.value, bool):
                if guard.value:
                    return dmbs
                return []
            # Over-approximate non-boolean literals instead of crashing
            return dmbs

        if isinstance(guard, UnaryExpression):
            if guard.op != "¬":
                # Over-approximate unrecognized unary operators
                return dmbs
            negated = self._negateExpression(guard.exp)
            if negated == guard:
                # Cannot structuraly negate further, over-approximate
                return dmbs
            return self._dedupeDMBs(self._applyConstraintExpressionToDMB(negated, dmbs, contextLocation, contextEdge))

        if isinstance(guard, BinaryExpression):
            match guard.op:
                case "∧":
                    dmbs = self._applyConstraintExpressionToDMB(guard.left, dmbs, contextLocation, contextEdge)
                    dmbs = self._applyConstraintExpressionToDMB(guard.right, dmbs, contextLocation, contextEdge)
                case "∨":
                    left = self._applyConstraintExpressionToDMB(guard.left, [copy.deepcopy(dmb) for dmb in dmbs], contextLocation, contextEdge)
                    right = self._applyConstraintExpressionToDMB(guard.right, [copy.deepcopy(dmb) for dmb in dmbs], contextLocation, contextEdge)
                    dmbs = left + right
                case "<" | "<=" | ">" | ">=" | "≥" | "≤":
                    for dmb in dmbs:
                        try:
                            self._applyComparisonConstraint(dmb, guard.left, guard.right, guard.op, contextLocation, contextEdge)
                        except ValueError:
                            # Over-approximate if comparison logic is non-affine, has missing constants, etc.
                            pass
                case _:
                    # Over-approximate unrecognized binary operators
                    return dmbs
            return self._dedupeDMBs(dmbs)

        # Over-approximate anything else (e.g. VariableReference)
        return dmbs
