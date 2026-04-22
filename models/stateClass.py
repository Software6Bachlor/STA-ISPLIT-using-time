from DMB import DBM
from dataclasses import dataclass

@dataclass
class StateClass:
    locationName: str
    dmb: DBM | None
    distance: int
