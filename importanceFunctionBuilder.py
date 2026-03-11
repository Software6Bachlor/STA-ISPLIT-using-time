from typing import Callable, List
from collections import deque

from models.stateSnapshot import StateSnapShot
from models.STA import Location, Edge, Automaton
from models.locationDistance import LocationDistance


def hopDistanceDictBuilder(
        rareEventLocation: Location,
        edges: List[Edge]
) -> dict[Location, int]:
    vistedSet = set()
    toVisitQueue = deque()
    hopDistanceDict: dict[Location, int] = {}
    rareEventStateScore = LocationDistance(rareEventLocation, 0)

    toVisitQueue.append(rareEventStateScore)

    while toVisitQueue:
        current: LocationDistance = toVisitQueue.popleft()

        vistedSet.add(current.location)
        hopDistanceDict[current.location] = current.distance

        # Add locations that have an edge going to current
        for edge in edges:
            if edge.location in vistedSet:
                continue

            if any(destination.location == current.location
                   for destination in edge.destinations):
                toVisitQueue.append(
                    LocationDistance(edge.location, current.distance + 1))

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
    toVisitQueue = deque()
    toVisitQueue.append(LocationDistance(Location("target"), 0))
    while toVisitQueue:
        # TODO: implement the backwards analysis to calculate the distance metric for each location
        current: LocationDistance = toVisitQueue.popleft()
        # Check if we have already visited this location
        # If we have, then check if we can merge
        # Cases
        # D1 subset D2 and d1 >= d2: keep Sigma2
        # D1 subset D2 and d1 < d2: keep Both since D1 has better distance for some cases
        # D1 intersect D2 != empty and d1 == d2: merge D's D1 union D2
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
