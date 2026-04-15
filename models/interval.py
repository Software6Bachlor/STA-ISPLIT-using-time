
class Interval:
    def __init__(self, lower: float, upper: float, include_lower: bool, include_upper: bool):
        

        self.upper: float = upper
        self.lower: float = lower
        self.include_upper: bool = include_upper
        self.include_lower: bool = include_lower
        
        if lower > upper:
            raise ValueError("Lower bound cannot be strictly greater than the upper bound.")


        def negate() -> Interval:
            pass



        


