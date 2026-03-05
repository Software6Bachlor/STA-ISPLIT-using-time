from dataclasses import dataclass
from models.STA import Location

@dataclass
class LocationDistance:
    location: Location
    distance: int
