from models.state import State

def test_clone():
    data = State(locations={'A': 'loc1'}, globalVars={'x': 10}, autoVars={'A': {'y': 5}}, pendingAssignments=[], recentAutomaton='A', globalTime=0.0)

    clone = data.clone()

    assert clone is not data
    assert clone.locations == data.locations
    assert clone.globalVars == data.globalVars
    assert clone.autoVars == data.autoVars
    assert clone.pendingAssignments == data.pendingAssignments
    assert clone.recentAutomaton == data.recentAutomaton
    assert clone.globalTime == data.globalTime

def test_setRecentAutomaton():
    data = State(locations={'A': 'loc1'}, recentAutomaton='A')
    data.setRecentAutomaton('B')
    assert data.recentAutomaton == 'B'

def test_setPendingAssignments():
    data = State(locations={'A': 'loc1'}, pendingAssignments=[])
    data.setPendingAssignments(['assignment1', 'assignment2'])
    assert data.pendingAssignments == ['assignment1', 'assignment2']

def test_getVariable():
    data = State(locations={'A': 'loc1'}, globalVars={'x': 10}, autoVars={'A': {'y': 5}}, recentAutomaton='A')
    assert data.getVariable('y') == 5
    assert data.getVariable('x') == 10
    assert data.getVariable('z') == None

def test_setVariable():
    data = State(locations={'A': 'loc1'}, globalVars={'x': 10}, autoVars={'A': {'y': 5}}, recentAutomaton='A')
    data.setVariable('y', 15)
    data.setVariable('x', 20)
    assert data.autoVars['A']['y'] == 15
    assert data.globalVars['x'] == 20

def test_handleBinaryExpression():
    from models.STA import BinaryExpression, VariableReference
    data = State(locations={'A': 'loc1'}, globalVars={'x': 10}, autoVars={'A': {'y': 5}}, recentAutomaton='A')
    expression = BinaryExpression(left=VariableReference('y'), op='+', right=VariableReference('x'))
    result = data.handleBinaryExpression(expression)
    assert result == 15

def test_evaluateExpression():
    from models.STA import Literal, VariableReference
    data = State(locations={'A': 'loc1'}, globalVars={'x': 10}, autoVars={'A': {'y': 5}}, recentAutomaton='A')
    literal_expr = Literal(42)
    var_ref_expr = VariableReference('y')
    assert data.evaluateExpression(literal_expr) == 42
    assert data.evaluateExpression(var_ref_expr) == 5