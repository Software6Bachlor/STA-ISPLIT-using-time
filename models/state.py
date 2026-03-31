import copy
from .STA import Assignment

class State:
    def __init__(self, locations: dict[str, str],
                 globalVars: dict[str: float] = None,
                 autoVars: dict[str, dict[str, float]]=None,
                 pendingAssignments: list[Assignment] = None,
                 recentAutomaton: str = None,
                 globalTime: float = 0
                 ):
        
        self.locations: dict[str, str] = locations                                                                       # e.g., {"Arrivals": "loc_1", "Server": "loc_1"}
        self.globalVars: dict[str, float] = globalVars if globalVars is not None else {}                                 # e.g., {"queue": 0, "served_customer": False}
        self.autoVars: dict[str, dict[str, float]] = autoVars if autoVars is not None else {}                            # e.g., {"Arrivals": {"c": 0, "x": 1.5}}
        self.globalTime: float = globalTime
        self.pendingAssignments: list[Assignment] = pendingAssignments if pendingAssignments is not None else {}         # A list of the assignments from recently taken edge                            
        self.recentAutomaton: str = recentAutomaton if recentAutomaton is not None else ""                               # Automaton of which most recent edge taken.

    def clone(self) -> 'State':
        newState = State()
        newState.locations = copy.deepcopy(self.locations)
        newState.globalVars = copy.deepcopy(self.globalVars)
        newState.autoVars = copy.deepcopy(self.autoVars)
        newState.globalTime = self.globalTime
        return newState

