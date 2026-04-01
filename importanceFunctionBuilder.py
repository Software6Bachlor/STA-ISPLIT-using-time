import copy
import logging
from typing import Callable, List
from collections import deque

from DMB import DMB
from models.stateSnapshot import StateSnapShot
from models.STA import Location, Edge, Automaton, Expression, BinaryExpression, Literal, VariableReference
from models.stateClass import StateClass

logger = logging.getLogger(__name__)


class ImportanceFunctionBuilder:
    def __init__(self, automaton: Automaton, rareEventLocation: Location):
        """Initialize builder state and precompute hop/time distance dictionaries."""
        self.automaton = automaton
        self.rareEventLocation = rareEventLocation
        self.hopDistanceDict = self._hopDistanceDictBuilder(self.rareEventLocation, automaton.edges)
        self.timeDistanceDict = self._timeDistanceDictBuilder(automaton, self.rareEventLocation)

    def build(self) -> Callable[[StateSnapShot], int]:
        """Return the callable importance function for state snapshots."""
        return self.importanceFunction

    def importanceFunction(self, snapShot: StateSnapShot) -> int:
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

    @staticmethod
    def _hopDistanceDictBuilder(
            rareEventLocation: Location,
            edges: List[Edge]
    ) -> dict[str, int]:
        """Build reverse-BFS hop distances from every location to the rare event location."""

        visitedSet = set()
        toVisitQueue: deque[StateClass] = deque()
        hopDistanceDict: dict[str, int] = {}
        rareEventStateScore = StateClass(rareEventLocation.name, None, 0)

        toVisitQueue.append(rareEventStateScore)

        while toVisitQueue:
            current: StateClass = toVisitQueue.popleft()

            visitedSet.add(current.locationName)
            hopDistanceDict[current.locationName] = current.distance

            # Add locations that have an edge going to current
            for edge in edges:
                if edge.location in visitedSet:
                    continue

                if any(destination.location == current.locationName
                       for destination in edge.destinations):
                    toVisitQueue.append(
                        StateClass(edge.location, None, current.distance + 1))

        return hopDistanceDict

    @classmethod
    def _timeDistanceDictBuilder(cls, automaton: Automaton, rareEventLocation: Location) -> dict[str, List[StateClass]]:
        """Perform backward analysis and build DMB-based distance classes per location."""
        statesToProcess: deque[StateClass] = deque()
        clocks = [variable.name for variable in automaton.variables
                  if variable.type == "clock"]
        targetStateClass = StateClass(rareEventLocation.name, DMB(clocks), 0)
        statesToProcess.append(targetStateClass)

        visitedDict: dict[str, List[StateClass]] = {targetStateClass.locationName: [targetStateClass]}

        while statesToProcess:
            current: StateClass = statesToProcess.popleft()

            # Find incoming edges to current location
            location = automaton.getLocationByName(current.locationName)
            if location is None:
                raise ValueError(f"Location {current.locationName} not found in automaton.")
            incomingEdges = automaton.getIncomingEdges(location)

            # For each incoming edge, calculate the new DMB and distance metric for the source location
            for edge in incomingEdges:
                incomingDMB = copy.deepcopy(current.dmb)
                if incomingDMB is None:
                    raise ValueError("DMB should not be None.")

                # Check for a clock reset and update the DMB accordingly
                cls._applyClockResets(incomingDMB, edge, current)

                # Apply the guards of the edge to update the DMB
                # TODO: Figure out if we need to do things with the other expressions
                incomingDMBs = cls._applyConstraintExpressionToDMB(edge.guard, [incomingDMB])

                # Apply source location invariant to the DMB
                sourceLocation = automaton.getLocationByName(edge.location)
                if sourceLocation is None:
                    raise ValueError(f"Source location {edge.location} not found in automaton.")
                incomingDMBs = cls._applyConstraintExpressionToDMB(sourceLocation.timeProgress, incomingDMBs)

                # Normilize the DMB
                validDMBs: List[DMB] = []
                for dmb in incomingDMBs:
                    dmb.normalize()

                    if dmb.isEmpty():
                        continue

                    dmb.removeLowerBounds()

                    dmb.normalize()

                    validDMBs.append(dmb)

                # TODO: prune clocks that are irrelevant for the state to save memory optional

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
                    mergedStateClasses = cls._mergeStateClasses(stateClasses, incommingStateClasses)
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
                case "<" | "<=":
                    # x <= c  ->  x - 0 <= c
                    dmb.addConstraint(left.name, "0", bound)
                case ">" | ">=":
                    # x >= c  ->  0 - x <= -c
                    dmb.addConstraint("0", left.name, -bound)
                case _:
                    raise ValueError(f"Unsupported comparison operator: {op}")
            return

        if isinstance(left, Literal) and isinstance(right, VariableReference):
            bound = float(left.value)
            match op:
                case "<" | "<=":
                    # c <= x  ->  0 - x <= -c
                    if op == "<":
                        logger.warning("Approximating strict inequality '<' as non-strict bounds in DMB: %s", f"{left.value} {op} {right.name}")
                    dmb.addConstraint("0", right.name, -bound)
                case ">" | ">=":
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
                case "<" | "<=" | ">" | ">=":
                    for dmb in dmbs:
                        cls._applyComparisonConstraint(dmb, guard.left, guard.right, guard.op)
                case _:
                    raise ValueError(f"Unsupported guard operation: {guard.op}")

        return dmbs
