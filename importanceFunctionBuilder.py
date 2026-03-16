import copy
import logging
from typing import Callable, List
from collections import deque

from DMB import DMB
from models.stateSnapshot import StateSnapShot
from models.STA import Location, Edge, Automaton, Expression, BinaryExpression, Literal, VariableReference
from models.stateClass import StateClass

logger = logging.getLogger(__name__)
#TODO: Make this into a class

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


def _timeDistanceDictBuilder(automaton: Automaton) -> dict[str, List[StateClass]]:
    # Input take a snapshot of the state and clocks <l tau>
    # To normalize these values such that 0 is closest to out goal
    # we want calculate to do the following:
    # 1. find the highst d(s') where s' in S with the higest value,
    # where d() is our distance metric.
    # 2. Then do d(s') - d(s) = score
    # This will lead to states far from max state gets large score
    # Things close to max state get small score, and max state get 0 score


    # To calculate the distance metric, we can:
    # Use SC thoery and run the backwards analysis from target location.
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
            for destination in edge.destinations:
                if destination.location.name == current.locationName:
                    for assignment in destination.assignments:
                        if not isinstance(assignment.value, Expression):
                            continue
                        if assignment.ref in clocks:
                            incommingDMB.removeConstrains(assignment.ref)

            # Apply the guards of the edge to update the DMB
            # TODO: Figure out if we need to do things with the other expressions
            incommingDMBs = _applyConstraintExpressionToDMB(edge.guard, [incommingDMB])

            # Apply source location invariant to the DMB
            incommingDMBs = _applyConstraintExpressionToDMB(location.timeProgress, incommingDMBs)

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
                vistedDict[edge.location.name] = _mergeStateClasses(stateClasses, incommingStateClasses)

    return vistedDict


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
                dmb.addConstraint("0", right.name, -bound)
            case ">" | ">=":
                # c >= x  ->  x - 0 <= c
                dmb.addConstraint(right.name, "0", bound)
            case _:
                raise ValueError(f"Unsupported comparison operator: {op}")
        return

    raise ValueError(f"Unsupported operands for '{op}' guard.")

def _applyConstraintExpressionToDMB(guard: Expression, dmbs: List[DMB]) -> List[DMB]:
    if isinstance(guard, BinaryExpression):
        match guard.op:
            case "∧":
                dmbs = _applyConstraintExpressionToDMB(guard.left, dmbs)
                dmbs = _applyConstraintExpressionToDMB(guard.right, dmbs)
            case "∨":
                left  = _applyConstraintExpressionToDMB(guard.left, [copy.deepcopy(dmb) for dmb in dmbs])
                right = _applyConstraintExpressionToDMB(guard.right, [copy.deepcopy(dmb) for dmb in dmbs])
                dmbs = left + right
            case "<":
                logger.warning("Approximating strict inequality '<' as non-strict bounds in DMB: %s", guard)
                for dmb in dmbs:
                    _applyComparisonConstraint(dmb, guard.left, guard.right, guard.op)
            case "<=":
                for dmb in dmbs:
                    _applyComparisonConstraint(dmb, guard.left, guard.right, guard.op)
            case ">":
                logger.warning("Approximating strict inequality '>' as non-strict bounds in DMB: %s", guard)
                for dmb in dmbs:
                    _applyComparisonConstraint(dmb, guard.left, guard.right, guard.op)
            case ">=":
                for dmb in dmbs:
                    _applyComparisonConstraint(dmb, guard.left, guard.right, guard.op)
            case _:
                raise ValueError(f"Unsupported guard operation: {guard.op}")

    return dmbs

def importanceFunctionBuilder(automaton: Automaton) -> Callable[[StateSnapShot], int]:
    hopDistanceDict = _hopDistanceDictBuilder(automaton.locations[0], automaton.edges)
    timeDistanceDict = _timeDistanceDictBuilder(automaton)

    def importanceFunction(snapShot: StateSnapShot) -> int:
        # Check for time distance score first
        locationName = StateSnapShot.stateName
        stateClasses = timeDistanceDict.get(locationName, None)
        if stateClasses is not None:
            holdingStateClasses = [stateClass for stateClass in stateClasses
                                   if stateClass.dmb is not None and
                                    stateClass.dmb.isSatisfiedBy(snapShot.clocks)]
            if holdingStateClasses:
                bestStateClass = min(holdingStateClasses, key=lambda sc: sc.distance)
                return bestStateClass.distance

        return hopDistanceDict[snapShot.stateName]

    return importanceFunction
