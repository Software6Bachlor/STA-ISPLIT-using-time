from dataclasses import dataclass
from STA import Location

@dataclass
class LocationDistance:
    location: Location
    distance: int
