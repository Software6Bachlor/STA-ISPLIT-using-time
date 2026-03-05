from typing import Callable, List
from collections import deque

from models.stateSnapshot import StateSnapShot
from models.STA import Location, Edge
from models.locationDistance import LocationDistance


def hopDistanceDictBuilder(
        startLocation: Location,
        edges: List[Edge]
) -> dict[Location, int]:
    vistedSet = set()
    toVisitQueue = deque()
    hopDistanceDict: dict[Location, int] = {}
    startStateScore = LocationDistance(startLocation, 0)

    toVisitQueue.append(startStateScore)

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
    return {}

def importanceFunctionBuilder() -> Callable[[StateSnapShot], int]:
    hopDistanceDict = hopDistanceDictBuilder()
    timeDistanceDict = timeDistanceDictBuilder()

    def importanceFunction(snapShot: StateSnapShot) -> int:
        if snapShot in timeDistanceDict:
            return timeDistanceDict[snapShot]

        hopDistanceDict[snapShot]

    return importanceFunction
