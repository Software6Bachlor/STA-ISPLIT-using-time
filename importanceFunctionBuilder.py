import copy
from typing import Callable, List
from collections import deque

from DMB import DMB
from models.stateSnapshot import StateSnapShot
from models.STA import Location, Edge, Automaton, Expression
from models.stateClass import StateClass
#TODO: Make this into a class

def hopDistanceDictBuilder(
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


def timeDistanceDictBuilder(automaton: Automaton) -> dict[StateSnapShot, int]:
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
            incommingStateClass = StateClass(edge.location.name, None, current.distance + 1)
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
            for guard in edge.guards:



            # If we have, then check if we can merge
            for stateClass in vistedDict[current.locationName]:
                # Cases
                # D1 subset D2 and d1 >= d2: keep Sigma2
                # D1 subset D2 and d1 < d2: keep Both since D1 has better distance for some cases
                # D1 intersect D2 != empty and d1 == d2: Keep both
                # D1 intersect D2 != empty and d1 != d2: Keep both
                # D1 intersect D2 == empty, keep both can not merge
                pass

        # If we have, then check if we can merge
        # Cases
        # D1 subset D2 and d1 >= d2: keep Sigma2
        # D1 subset D2 and d1 < d2: keep Both since D1 has better distance for some cases
        # D1 intersect D2 != empty and d1 == d2: Keep both
        # D1 intersect D2 != empty and d1 != d2: Keep both
        # D1 intersect D2 == empty, keep both can not merge
        pass


    return {}

def importanceFunctionBuilder(automaton: Automaton) -> Callable[[StateSnapShot], int]:
    hopDistanceDict = hopDistanceDictBuilder(automaton.locations[0], automaton.edges)
    timeDistanceDict = timeDistanceDictBuilder(automaton)

    def importanceFunction(snapShot: StateSnapShot) -> int:
        score: int
        if snapShot in timeDistanceDict:
            return timeDistanceDict[snapShot]

        return hopDistanceDict[snapShot]

    return importanceFunction
