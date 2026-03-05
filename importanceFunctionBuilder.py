from typing import Callable, List, Set
from stateSnapshot import StateSnapShot
from collections import deque
from dataclasses import dataclass

@dataclass
class StateDistance:
    state: str
    distance: int

def hopDistanceDictBuilder(
        startState: str,
        states: List[str],
        edges: dict[str, List[str]]
) -> dict[str, int]:
    vistedSet = set()
    toVisitQueue = deque()
    hopDistanceDict: dict[str, int] = {}
    startStateScore = StateDistance(startState, 0)

    toVisitQueue.append(startStateScore)

    while toVisitQueue.count != 0:
        stateDistance: StateDistance = toVisitQueue.popleft()

        vistedSet.add(stateDistance.state)
        hopDistanceDict[stateDistance.state] = stateDistance.distance

        # Add neighbors to to visit queue
        toVisitQueue.extend([StateDistance(neighbor, stateDistance.distance + 1) for neighbor in edges[stateDistance.state] if neighbor not in vistedSet])

    return hopDistanceDict

def timeDistanceDictBuilder() -> dict[(str, List[(str, float)]), int]:
    return {}

def importanceFunctionBuilder() -> Callable[[StateSnapShot], int]:
    hopDistanceDict = hopDistanceDictBuilder()
    timeDistanceDict = timeDistanceDictBuilder()

    def importanceFunction(snapShot: StateSnapShot) -> int:
        if snapShot in timeDistanceDict:
            return timeDistanceDict[snapShot]

        hopDistanceDict[snapShot]

    return importanceFunction
