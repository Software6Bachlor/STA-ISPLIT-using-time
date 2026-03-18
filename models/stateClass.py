from DMB import DMB
from dataclasses import dataclass

@dataclass
class StateClass:
    locationName: str
    dmb: DMB | None
    distance: int
