from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class Constant:
    name: str
    type: int

@dataclass
class VariableType:
    kind: str
    base: int
    lower_bound: int
    upper_bound: int

@dataclass
class Variable:
    name: str
    type: Any
    initial_value: Optional[Any] = None
    transient: Optional[bool] = False

@dataclass
class Literal:
    value: Any

@dataclass
class VariableReference:
    name: str

@dataclass
class BinaryExpression:
    op: str
    left: Expression
    right: Expression

@dataclass
class IfThenElse:
    condition: Expression
    then: Expression
    else_: Expression

Expression = Literal | BinaryExpression | IfThenElse | VariableReference

@dataclass
class PropertyExpression:
    op: str
    operands: dict[str, Any]

@dataclass
class Property:
    name: str
    expression: PropertyExpression

@dataclass
class Location:
    name: str
    timeProgress: Expression

@dataclass
class Distribution:
    type: str
    args: list[Expression]

@dataclass
class Assignment:
    ref: str
    value: Expression | Distribution

@dataclass
class Destination:
    location: str
    assignments: list[Assignment]

@dataclass
class Edge:
    from .state import State
    location: str
    guard: Expression
    destinations: list[Destination]

    def calculateTimeUntilValid(self, guard: Expression, state: State, automaton: Automaton) -> Optional[float]:
        
        def evaluate_term(expr: 'Expression') -> tuple[float, float]:
            """Returns (current_value, rate_of_change) for a mathematical expression."""
            
            if isinstance(expr, Literal):
                return float(expr.value), 0.0
                
            if isinstance(expr, VariableReference):
                var_name = expr.name
                
                # 1. Check if it's a global variable (rate is 0.0)
                if var_name in state.globalVars:
                    return float(state.globalVars[var_name]), 0.0
                    
                # 2. Check if it's an automaton variable
                if var_name in state.autoVars[automaton.name]:
                    val = float(state.autoVars[automaton.name][var_name])
                    
                    # Determine if it's a clock to set the rate of change
                    is_clock = False
                    for v in automaton.variables:
                        if v.name == var_name and getattr(v, 'type', '') == "clock":
                            is_clock = True
                            break
                            
                    return val, 1.0 if is_clock else 0.0
                    
            if isinstance(expr, BinaryExpression):
                l_val, l_rate = evaluate_term(expr.left)
                r_val, r_rate = evaluate_term(expr.right)
                
                if expr.op == '+': return l_val + r_val, l_rate + r_rate
                if expr.op == '-': return l_val - r_val, l_rate - r_rate
                
            raise ValueError(f"Unsupported term for evaluation: {expr}")
        
        def solve_guard(expr: 'Expression') -> Optional[float]:
            """Returns the minimum time 't' >= 0 for the expression to be True, or None if impossible."""
            if isinstance(expr, Literal):
                # If the literal is a boolean True, it's valid immediately (0.0). False is impossible (None).
                return 0.0 if expr.value else None
                
            if isinstance(expr, BinaryExpression):
                op = expr.op
                
                # --- LOGICAL OPERATORS ---
                if op == '∧':  # AND
                    t_left = solve_guard(expr.left)
                    t_right = solve_guard(expr.right)
                    if t_left is None or t_right is None:
                        return None
                    return max(t_left, t_right)
                    
                if op == '∨':  # OR
                    t_left = solve_guard(expr.left)
                    t_right = solve_guard(expr.right)
                    if t_left is None: return t_right
                    if t_right is None: return t_left
                    return min(t_left, t_right)

                # --- RELATIONAL OPERATORS ---
                l_val, l_rate = evaluate_term(expr.left)
                r_val, r_rate = evaluate_term(expr.right)
                
                # Calculate required change (V) and combined rate of change (R)
                R = l_rate - r_rate
                V = r_val - l_val
                
                if op in ('≥', '>=', '>', 'greater'):
                    if R > 0: return max(0.0, V / R)
                    if R < 0: return 0.0 if (V / R) >= 0 else None
                    if R == 0: return 0.0 if 0 >= V else None
                    
                if op in ('≤', '<=', '<', 'less'):
                    if R > 0: return 0.0 if (V / R) >= 0 else None
                    if R < 0: return max(0.0, V / R)
                    if R == 0: return 0.0 if 0 <= V else None
                    
                if op in ('=', '==', 'eq'):
                    if R != 0: 
                        t = V / R
                        return t if t >= 0 else None
                    if R == 0: return 0.0 if 0 == V else None

            raise ValueError(f"Unsupported guard expression: {expr}")

        if not guard:
            return 0.0
            
        return solve_guard(guard)

@dataclass
class Automaton:
    name: str
    locations: list[Location]
    initial_locations: list[Location]
    variables: list[Variable]
    edges: list[Edge]

@dataclass
class Element:
    automaton: str

@dataclass
class System:
    elements: list[Element]

@dataclass
class Model:
    jani_version: str
    name: str
    type: str
    features: Optional[list[str]] = None
    constants: Optional[list[Constant]] = None
    variables: Optional[list[Variable]] = None
    properties: Optional[list[Property]] = None
    automata: list[Automaton] = None
    system: System = None