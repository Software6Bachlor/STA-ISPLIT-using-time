import copy
from typing import Optional, Any, List
from models.stateSnapshot import StateSnapShot
from models.clock import Clock

from .STA import Assignment, BinaryExpression, Expression, Literal, VariableReference, Distribution

#TODO Ændre så vars kan være bools i stedet for kun floats.
class State:
    def __init__(self, locations: dict[str, str], 
                 globalVars: dict[str, float] = None,
                 autoVars: dict[str, dict[str, float]] = None,
                 pendingAssignments: list[Assignment] = None,
                 recentAutomaton: str = None,
                 globalTime: float = 0
                 ):
        
        self.locations: dict[str, str] = locations                                                                       # e.g., {"Arrivals": "loc_1", "Server": "loc_1"}
        self.globalVars: dict[str, float] = globalVars if globalVars is not None else {}                                 # e.g., {"queue": 0, "served_customer": False}
        self.autoVars: dict[str, dict[str, float]] = autoVars if autoVars is not None else {}                            # e.g., {"Arrivals": {"c": 0, "x": 1.5}}
        self.globalTime: float = globalTime
        self.pendingAssignments: list[Assignment] = pendingAssignments if pendingAssignments is not None else []         # A list of the assignments from recently taken edge                            
        self.recentAutomaton: str = recentAutomaton                               # Automaton of which most recent edge taken.

    def clone(self) -> 'State':
        """
        Makes a completely independent deep copy of the current state.
        """
        newState = State(locations=copy.deepcopy(self.locations),
                         globalVars=copy.deepcopy(self.globalVars),
                         autoVars=copy.deepcopy(self.autoVars),
                         pendingAssignments=copy.deepcopy(self.pendingAssignments),
                         recentAutomaton=copy.deepcopy(self.recentAutomaton),
                         globalTime=copy.deepcopy(self.globalTime)
                         )
        return newState
    
    def setRecentAutomaton(self, name: str):
        """
        Takes an automaton name, and sets the automaton of the state to it.
        """
        self.recentAutomaton = name
    
    def setPendingAssignments(self, assignments: list[Assignment]):
        """
        Takes a list of assignments, and sets the pendingAssignments of the state to it.
        """
        self.pendingAssignments = assignments
    
    def getVariable(self, name: str) -> Optional[Any]:
        """
        Takes a name of a variable, and returns the local variable of present, else global variable. if no global variable, it returns None.
        """
        # first lookup local vars
        if name in self.autoVars[self.recentAutomaton]:
            return self.autoVars[self.recentAutomaton][name]
        # global
        if name in self.globalVars:
            return self.globalVars[name]
        return None
    
    def setVariable(self, name: str, value: float):
        """
        Takes a name of the variable, and the value. Then sets the variable located in the automaton/global variable to the specified value.
        """
        # first lookup local vars
        if name in self.autoVars[self.recentAutomaton]:
            self.autoVars[self.recentAutomaton][name] = value
        # global
        elif name in self.globalVars:
            self.globalVars[name] = value
        
    def handleBinaryExpression(self, expression: BinaryExpression) -> float:
        """
        Takes a binary expression, and returns the evaluated result as a float.
        """
        left_value = self.evaluateExpression(expression.left)
        right_value = self.evaluateExpression(expression.right)
        if expression.op == '+':
            return left_value + right_value
        elif expression.op == '-':
            return left_value - right_value
        elif expression.op == '*':
            return left_value * right_value
        elif expression.op == '/':
            return left_value / right_value
        else:
            raise ValueError(f"Unsupported operator: {expression.op}")
        
    def evaluateExpression(self, expression: Any) -> float:
        """
        Evaluates an expression, and returns the result as a float.
        """
        if isinstance(expression, BinaryExpression):
            return self.handleBinaryExpression(expression)
        elif isinstance(expression, VariableReference):
            return self.getVariable(expression.name)
        elif isinstance(expression, Literal):
            return expression.value
        else:
            raise ValueError(f"Unsupported expression type: {type(expression)}")
        
    def _createSnapshot(self, rareEventAutomation: str, clockNames: List[str]) -> StateSnapShot:
        snapshot = StateSnapShot(locationName=self.locations[rareEventAutomation], clocks=[])   
        for clockName in clockNames:
            clock = Clock(name=clockName, value=None)
            if clockName in self.autoVars[rareEventAutomation]:
                clock.value = self.autoVars[rareEventAutomation][clockName]
            elif clockName in self.globalVars:
                clock.value = self.globalVars[clockName]
            else:
                raise ValueError(f"Clock variable '{clockName}' not found in either automaton or global variables.")
            snapshot.clocks.append(clock)
        return snapshot