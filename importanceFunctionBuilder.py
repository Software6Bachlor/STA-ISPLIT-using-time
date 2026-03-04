from typing import Callable, List
from stateSnapshot import StateSnapShot

def hopDistanceMapBuilder() -> dict[str, int]:
    return {}

def timeDistanceMapBuilder() -> dict[(str, List[(str, float)]), int]:
    return {}

def importanceFunctionBuilder() -> Callable[[StateSnapShot], int]:
    hopDistanceMap = hopDistanceMapBuilder()
    timeDistanceMap = timeDistanceMapBuilder()

    def importanceFunction(snapShot : StateSnapShot) -> int:
        if snapShot in timeDistanceMap:
            return timeDistanceMap[snapShot]

        hopDistanceMap[snapShot]

    return importanceFunction
