import copy
class State:
    def __init__(self):
        self.locations: dict[str, str] = {}                 # e.g., {"Arrivals": "loc_1", "Server": "loc_1"}
        self.globalVars: dict[str, float] = {}             # e.g., {"queue": 0, "served_customer": False}
        self.autoVars: dict[str, dict[str, float]] = {}    # e.g., {"Arrivals": {"c": 0, "x": 1.5}}
        self.globalTime: float = 0.0

    def clone(self) -> 'State':
        newState = State()
        newState.locations = copy.deepcopy(self.locations)
        newState.globalVars = copy.deepcopy(self.globalVars)
        newState.autoVars = copy.deepcopy(self.autoVars)
        newState.globalTime = self.globalTime
        return newState

