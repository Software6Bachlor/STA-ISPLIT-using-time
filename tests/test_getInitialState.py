def test_getInitialState_returnsInitialState():
    from models.STA import Model, Literal
    from parser import parseModel
    from loader import loadData
    from utilities.get_initial_state import get_initial_state
    from models.state import State
    
    data = loadData("tests//testdata//ModestSTA.jani")  
    model: Model = parseModel(data)

    init_state: State = get_initial_state(model)

    assert init_state.locations == {"Arrivals": "loc_1", "Server": "loc_1"}
    assert init_state.autoVars == {'Arrivals': {'c': 0.0, 'x': 0.0}, 'Server': {'c': 0.0, 'x': 0.0}}
    assert init_state.globalVars == {'queue': 0.0, 'served_customer': 0.0}
    assert init_state.pendingAssignments == []
    assert init_state.recentAutomaton == None
    assert init_state.globalTime == 0

def test_getInitialState_returnsInitialStateWithDistribution():
    from models.STA import Model, Literal
    from parser import parseModel
    from loader import loadData
    from utilities.get_initial_state import get_initial_state
    from models.state import State
    

    data = loadData("tests//testdata//manufacturing-sta.jani")  
    model: Model = parseModel(data)

    init_state: State = get_initial_state(model)

    assert init_state.locations == {'Idle': 'loc_1'}

    # x is distrubution variable.
    assert init_state.autoVars["Idle"]["x"] < 5
    assert init_state.autoVars["Idle"]["x"] > 2