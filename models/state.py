import copy
from typing import Optional, Any

from .STA import IfThenElse, Assignment, BinaryExpression, Expression, Literal, VariableReference, Distribution

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
                         recentAutomaton=self.recentAutomaton,
                         globalTime=self.globalTime)
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
        elif expression.op == '<':
            return left_value < right_value
        elif expression.op == '>':
            return left_value > right_value
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
        elif isinstance(expression, IfThenElse):
            condition_value = self.evaluateExpression(expression.condition)
            if condition_value:
                return self.evaluateExpression(expression.then)
            else:
                return self.evaluateExpression(expression.else_)
        else:
            raise ValueError(f"Unsupported expression type: {type(expression)}")
        
    def get_signature(self) -> str:
        """
        Creates a unique, deterministic string representing the state.
        """
        # 1. Locations (Sorted to guarantee identical strings for identical states)
        locs_str = ",".join([f"{k}:{v}" for k, v in sorted(self.locations.items())])
        
        # 2. Global Variables (Sorted)
        gvars_str = ",".join([f"{k}:{v}" for k, v in sorted(self.globalVars.items())])
        
        # 3. Local Variables (Sorted Automaton by Automaton)
        lvars_parts = []
        for aut_name in sorted(self.autoVars.keys()):
            aut_vars = ",".join([f"{k}:{v}" for k, v in sorted(self.autoVars[aut_name].items())])
            lvars_parts.append(f"{aut_name}[{aut_vars}]")
        lvars_str = "|".join(lvars_parts)
        
        return f"L=({locs_str})||G=({gvars_str})||A=({lvars_str})"