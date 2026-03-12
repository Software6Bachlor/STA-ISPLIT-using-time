from typing import Callable, List
from collections import deque

from models.stateSnapshot import StateSnapShot
from models.STA import Location, Edge, Automaton
from models.stateClass import StateClass


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

        vistedSet.add(current.location)
        hopDistanceDict[current.location] = current.distance

        # Add locations that have an edge going to current
        for edge in edges:
            if edge.location.name in vistedSet:
                continue

            if any(destination.location.name == current.location
                   for destination in edge.destinations):
                toVisitQueue.append(
                    StateClass(edge.location.name, None, current.distance + 1))

    return hopDistanceDict


def timeDistanceDictBuilder() -> dict[Location, int]:
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
    toVisitQueue.append(StateClass("target", None, 0))
    while toVisitQueue:
        # TODO: implement the backwards analysis to calculate the distance metric for each location
        current: StateClass = toVisitQueue.popleft()
        # Check if we have already visited this location
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
    timeDistanceDict = timeDistanceDictBuilder()

    def importanceFunction(snapShot: StateSnapShot) -> int:
        score: int
        if snapShot in timeDistanceDict:
            return timeDistanceDict[snapShot]

        return hopDistanceDict[snapShot]

    return importanceFunction
