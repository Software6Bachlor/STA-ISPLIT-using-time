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
    def __init__(self, automaton: Automaton):
        self.automaton = automaton
        self.hopDistanceDict = self._hopDistanceDictBuilder(automaton.locations[0], automaton.edges)
        self.timeDistanceDict = self._timeDistanceDictBuilder(automaton)

    def build(self) -> Callable[[StateSnapShot], int]:
        return self.importanceFunction

    def importanceFunction(self, snapShot: StateSnapShot) -> int:
        # Check for time distance score first
        locationName = snapShot.stateName
        stateClasses = self.timeDistanceDict.get(locationName, None)
        if stateClasses is not None:
            holdingStateClasses = [stateClass for stateClass in stateClasses
                                   if stateClass.dmb is not None and
                                   stateClass.dmb.isSatisfiedBy(snapShot.clocks)]
            if holdingStateClasses:
                bestStateClass = min(holdingStateClasses, key=lambda sc: sc.distance)
                return bestStateClass.distance
            return int(1e9)  # No time-distance class applies, return a large number to indicate low importance
        return self.hopDistanceDict[snapShot.stateName]

    @staticmethod
    def _hopDistanceDictBuilder(
            rareEventLocation: Location,
            edges: List[Edge]
    ) -> dict[str, int]:

        vistedSet = set()
        toVisitQueue: deque[StateClass] = deque()
        hopDistanceDict: dict[str, int] = {}
        rareEventStateScore = StateClass(rareEventLocation.name, None, 0)

        toVisitQueue.append(rareEventStateScore)

        while toVisitQueue:
            current: StateClass = toVisitQueue.popleft()

            vistedSet.add(current.locationName)
            hopDistanceDict[current.locationName] = current.distance

            # Add locations that have an edge going to current
            for edge in edges:
                if edge.location.name in vistedSet:
                    continue

                if any(destination.location.name == current.locationName
                       for destination in edge.destinations):
                    toVisitQueue.append(
                        StateClass(edge.location.name, None, current.distance + 1))

        return hopDistanceDict

    @classmethod
    def _timeDistanceDictBuilder(cls, automaton: Automaton) -> dict[str, List[StateClass]]:
        """ Performs a backwards analysis to calculate the distance metric for each location in the automaton. """
        toVisitQueue: deque[StateClass] = deque()
        clocks = [variable.name for variable in automaton.variables
                  if variable.type == "clock"]
        toVisitQueue.append(StateClass("target", DMB(clocks), 0))

        vistedDict: dict[str, List[StateClass]] = {}

        while toVisitQueue:
            # TODO: implement the backwards analysis to calculate the distance metric for each location
            current: StateClass = toVisitQueue.popleft()
            vistedDict[current.locationName] = vistedDict.get(current.locationName, []) + [current]

            # Find incoming edges to current location
            location = automaton.getLocationByName(current.locationName)
            if location is None:
                raise ValueError(f"Location {current.locationName} not found in automaton.")
            incomingEdges = automaton.getIncomingEdges(location)

            # For each incoming edge, calculate the new DMB and distance metric for the source location
            for edge in incomingEdges:
                incommingDMB = copy.deepcopy(current.dmb)
                if incommingDMB is None:
                    raise ValueError("DMB should not be None.")

                # Check for a clock reset and update the DMB accordingly
                cls._applyClockResets(incommingDMB, edge, current)

                # Apply the guards of the edge to update the DMB
                # TODO: Figure out if we need to do things with the other expressions
                incommingDMBs = cls._applyConstraintExpressionToDMB(edge.guard, [incommingDMB])

                # Apply source location invariant to the DMB
                incommingDMBs = cls._applyConstraintExpressionToDMB(location.timeProgress, incommingDMBs)

                # Normilize the DMB
                for dmb in incommingDMBs:
                    dmb.normalize()

                # TODO: prune clocks that are irrelevant for the state to save memory optional

                # Construct new stateClasses
                incommingStateClasses = [
                    StateClass(edge.location.name, dmb, current.distance + 1)
                    for dmb in incommingDMBs]

                # Check if we have already visited the source location with a DMB
                stateClasses = vistedDict.get(edge.location.name, None)
                if stateClasses is None:
                    vistedDict[edge.location.name] = incommingStateClasses
                else:
                    vistedDict[edge.location.name] = cls._mergeStateClasses(stateClasses, incommingStateClasses)

        return vistedDict

    @staticmethod
    def _applyClockResets(dmb: DMB, edge: Edge, current: StateClass) -> None:
        for destination in edge.destinations:
            if destination.location.name == current.locationName:
                for assignment in destination.assignments:
                    if not isinstance(assignment.value, Expression):
                        continue
                    if assignment.ref in dmb.clocks:
                        dmb.removeConstrains(assignment.ref)

    @staticmethod
    def _mergeStateClasses(existing: List[StateClass], incoming: List[StateClass]) -> List[StateClass]:
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
        if isinstance(left, VariableReference) and isinstance(right, Literal):
            bound = int(right.value)
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
            bound = int(left.value)
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
    def _applyConstraintExpressionToDMB(cls, guard: Expression, dmbs: List[DMB]) -> List[DMB]:
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
