from typing import List
from models.clock import Clock
from dataclasses import dataclass

@dataclass
class StateSnapShot:
    locationName: str
    clocks: List[Clock]
