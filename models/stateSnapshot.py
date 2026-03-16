from typing import List
from clock import Clock
from dataclasses import dataclass

@dataclass
class StateSnapShot:
    stateName: str
    clocks: List[Clock]
