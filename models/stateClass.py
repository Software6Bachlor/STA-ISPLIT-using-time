from DMB import DMB
from dataclasses import dataclass

@dataclass
class StateClass:
    location: str
    dmb: DMB | None
    distance: int
