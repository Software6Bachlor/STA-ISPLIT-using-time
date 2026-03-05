from typing import List
from dataclasses import dataclass

Clock = tuple[str, float]

@dataclass
class StateSnapShot:
    stateName: str
    clocks: List[Clock]
