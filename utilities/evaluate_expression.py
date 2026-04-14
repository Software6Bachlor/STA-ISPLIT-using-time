from models.STA import Expression, Literal, BinaryExpression, VariableReference
from typing import Optional, Any
from models.state import State

def evaluate_expression(expression: Expression, state: State) -> Optional[Any]:
    
    if(isinstance(expression, Literal)):
        return expression.value
    
    elif(isinstance(expression, BinaryExpression)):
        left = evaluate_expression(expression.left, state)
        right = evaluate_expression(expression.right, state)
        if expression.op == '+':
            return left + right
        elif expression.op == '-':
            return left - right
        elif expression.op == '*':
            return left * right
        elif expression.op == '/':
            return left / right
        else:
            raise ValueError(f"Unsupported operator: {expression.op}")
        
    if(isinstance(expression, VariableReference)):
        if state is not None:
            return state.getVariable(expression.name)
        else:
            raise ValueError(f"VariableReference when no state provided not allowed.")
            
    raise ValueError(f"Unsupported expression type: {type(expression)}")
