
class Interval:
    def __init__(self, lower: float, upper: float, include_lower: bool, include_upper: bool):
        self.upper: float = upper
        self.lower: float = lower
        self.include_upper: bool = include_upper
        self.include_lower: bool = include_lower
        
        if lower > upper:
            raise ValueError("Lower bound cannot be strictly greater than the upper bound.")


    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Interval):
            return False
        return (self.lower == other.lower and
                self.upper == other.upper and
                self.include_lower == other.include_lower and
                self.include_upper == other.include_upper)

    def __repr__(self) -> str:
        """Tells pytest and lists how to display this object."""
        return f"Interval({self.lower}, {self.upper}, {self.include_lower}, {self.include_upper})"
        


