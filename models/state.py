import copy
from typing import Optional, Any

from utilities.sample_distribution import sample_distribution
from .STA import Assignment, BinaryExpression, Expression, Literal, VariableReference, Distribution

#TODO Ændre så vars kan være bools i stedet for kun floats.
class State:
    def __init__(self, locations: dict[str, str], 
                 globalVars: dict[str: float] = None,
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
        newState = State()
        newState.locations = copy.deepcopy(self.locations)
        newState.globalVars = copy.deepcopy(self.globalVars)
        newState.autoVars = copy.deepcopy(self.autoVars)
        newState.globalTime = self.globalTime
        return newState
    
    def setRecentAutomaton(self, name: str):
        self.recentAutomaton = name
    
    def setPendingAssignments(self, assignments: list[Assignment]):
        self.pendingAssignments = assignments
    
    def getVariable(self, name: str) -> Optional[Any]:
        # first lookup local vars
        if name in self.autoVars[self.recentAutomaton]:
            return self.autoVars[self.recentAutomaton][name]
        # global
        if name in self.globalVars:
            return self.globalVars[name]
        return None
    
    def setVariable(self, name: str, value: float):
        # first lookup local vars
        print(name)
        if name in self.autoVars[self.recentAutomaton]:
            self.autoVars[self.recentAutomaton][name] = value
        # global
        elif name in self.globalVars:
            self.globalVars[name] = value

    def handlePendingAssignments(self):
        for assignment in self.pendingAssignments:
            value: float
            if isinstance(assignment.value, Distribution):
                value = sample_distribution(assignment.value)
            elif isinstance(assignment.value, Expression):
                value = self.evaluateExpression(assignment.value)
            self.setVariable(assignment.ref, value)
        
    def handleBinaryExpression(self, expression: BinaryExpression) -> float:
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
        if isinstance(expression, BinaryExpression):
            return self.handleBinaryExpression(expression)
        elif isinstance(expression, VariableReference):
            return self.getVariable(expression.name)
        elif isinstance(expression, Literal):
            return expression.value
        else:
            raise ValueError(f"Unsupported expression type: {type(expression)}")
        
