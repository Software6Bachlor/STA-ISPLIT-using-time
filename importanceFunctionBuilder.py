import copy, logging, psutil
from typing import Callable, List
from collections import deque

from DMB import DMB
from models.stateSnapshot import StateSnapShot
from models.STA import *
from models.stateClass import StateClass

logger = logging.getLogger(__name__)


class ImportanceFunctionBuilder:
    def __init__(self, automaton: Automaton, rareEventLocationName: str, mbLimit: int):
        """Initialize builder state and precompute hop/time distance dictionaries."""
        self.automaton = automaton
        rareEventLocation = self.automaton.getLocationByName(rareEventLocationName)
        if rareEventLocation is None:
            raise ValueError(f"Rare event location '{rareEventLocationName}' not found in automaton.")
        self.rareEventLocation = rareEventLocation
        self.mbLimit = mbLimit
        self.hopDistanceDict = self._hopDistanceDictBuilder()
        self.timeDistanceDict = self._timeDistanceDictBuilder()

    def build(self) -> Callable[[StateSnapShot], int]:
        """Return the callable importance function for state snapshots."""
        return self._importanceFunction

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
        clocks = [variable.name for variable in self.automaton.variables
                  if variable.type == "clock"]
        targetStateClass = StateClass(self.rareEventLocation.name, DMB(clocks), 0)
        statesToProcess.append(targetStateClass)

        visitedDict: dict[str, List[StateClass]] = {targetStateClass.locationName: [targetStateClass]}

        while statesToProcess:
            print(f"Memory used: {psutil.Process().memory_info().rss / (1024 * 1024):.2f} MB, Queue size: {len(statesToProcess)}, Visited locations: {len(visitedDict)}")
            current: StateClass = statesToProcess.popleft()

            # Find incoming edges to current location
            location = self.automaton.getLocationByName(current.locationName)
            if location is None:
                raise ValueError(f"Location {current.locationName} not found in automaton.")
            incomingEdges = self.automaton.getIncomingEdges(location)

            # For each incoming edge, calculate the new DMB and distance metric for the source location
            for edge in incomingEdges:
                incomingDMB = copy.deepcopy(current.dmb)
                if incomingDMB is None:
                    raise ValueError("DMB should not be None.")

                # Check for a clock reset and update the DMB accordingly
                self._applyClockResets(incomingDMB, edge, current)

                # Apply the guards of the edge to update the DMB
                # TODO: Figure out if we need to do things with the other expressions
                incomingDMBs = self._applyConstraintExpressionToDMB(edge.guard, [incomingDMB])

                # Apply source location invariant to the DMB
                sourceLocation = self.automaton.getLocationByName(edge.location)
                if sourceLocation is None:
                    raise ValueError(f"Source location {edge.location} not found in automaton.")
                incomingDMBs = self._applyConstraintExpressionToDMB(sourceLocation.timeProgress, incomingDMBs)

                # Normilize the DMB
                validDMBs: List[DMB] = []
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

    def _getClockNames(self) -> List[str]:
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

                # Gaurded on
                for assignment in destination.assignments:
                    if isinstance(assignment.value, Expression):
                        for name in self._findVariableReferenceNames(assignment.value):
                            addToAppearances(name, 1, destination.location)

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
            location = self.automaton.getLocationByName(guardedOn.pop())
            if location is None:
                raise ValueError(f"Location {guardedOn.pop()} not found in automaton.")

            if not all(edge in resetOn for edge in self.automaton.getIncomingEdges(location)):
                nonLocalClockNames.append(clockName)
                continue
            logger.info(f"Clock '{clockName}' is identified as a local sojourn clock for location '{location.name}' and will be ignored in the importance function.")

        accumulatorNames = [variable.name for variable in self.automaton.variables if variable.accumulator]

        return nonLocalClockNames + accumulatorNames


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


    def _findNamesAssignedZero(self, assignments: List[Assignment]) -> list[str]:
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


    @staticmethod
    def _applyClockResets(dmb: DMB, edge: Edge, current: StateClass) -> None:
        """
        Apply clock resets on the transition into the current location by freeing reset clocks.
        """
        for destination in edge.destinations:
            if destination.location == current.locationName:
                for assignment in destination.assignments:
                    if not isinstance(assignment.value, Expression):
                        continue
                    if assignment.ref in dmb.clocks:
                        dmb.removeConstrains(assignment.ref)

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
    def _applyComparisonConstraint(dmb: DMB, left: Expression, right: Expression, op: str) -> None:
        """Translate a comparison expression into one or more DMB constraints."""
        if isinstance(left, VariableReference) and isinstance(right, Literal):
            bound = float(right.value)
            match op:
                case "<" | "<=" | "≤":
                    # x <= c  ->  x - 0 <= c
                    dmb.addConstraint(left.name, "0", bound)
                case ">" | ">=" | "≥":
                    # x >= c  ->  0 - x <= -c
                    dmb.addConstraint("0", left.name, -bound)
                case _:
                    raise ValueError(f"Unsupported comparison operator: {op}")
            return

        if isinstance(left, Literal) and isinstance(right, VariableReference):
            bound = float(left.value)
            match op:
                case "<" | "<=" | "≤":
                    # c <= x  ->  0 - x <= -c
                    if op == "<":
                        logger.warning("Approximating strict inequality '<' as non-strict bounds in DMB: %s", f"{left.value} {op} {right.name}")
                    dmb.addConstraint("0", right.name, -bound)
                case ">" | ">=" | "≥":
                    # c >= x  ->  x - 0 <= c
                    if op == ">":
                        logger.warning("Approximating strict inequality '>' as non-strict bounds in DMB: %s", f"{left.value} {op} {right.name}")
                    dmb.addConstraint(right.name, "0", bound)
                case _:
                    raise ValueError(f"Unsupported comparison operator: {op}")
            return
        raise ValueError(f"Unsupported operands for '{op}' guard.")

    @classmethod
    def _applyConstraintExpressionToDMB(cls, guard: Expression | None, dmbs: List[DMB]) -> List[DMB]:
        """Apply guard constraints to DMBs, supporting conjunction, disjunction, and comparisons."""
        if guard is None:
            return dmbs

        if isinstance(guard, BinaryExpression):
            match guard.op:
                case "∧":
                    dmbs = cls._applyConstraintExpressionToDMB(guard.left, dmbs)
                    dmbs = cls._applyConstraintExpressionToDMB(guard.right, dmbs)
                case "∨":
                    left = cls._applyConstraintExpressionToDMB(guard.left, [copy.deepcopy(dmb) for dmb in dmbs])
                    right = cls._applyConstraintExpressionToDMB(guard.right, [copy.deepcopy(dmb) for dmb in dmbs])
                    dmbs = left + right
                case "<" | "<=" | ">" | ">=" | "≥" | "≤":
                    for dmb in dmbs:
                        cls._applyComparisonConstraint(dmb, guard.left, guard.right, guard.op)
                case _:
                    raise ValueError(f"Unsupported guard operation: {guard.op}")

        return dmbs
