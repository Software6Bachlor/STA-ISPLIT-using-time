from typing import List

Clock = tuple[str, float]

class StateSnapShot:
    def __init__(self,
                 stateName : str,
                 clocks : List[Clock] ):
        self.stateName = stateName,
        self.clocks = clocks
