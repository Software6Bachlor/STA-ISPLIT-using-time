def test_restart_transient_variables():
    from models.simulation import STASimulator, State
    from models.STA import Model
    from parser import parse_model
    from loader import load_data

    data = load_data("tests//testdata//ModestSTA.jani")  
    model = parse_model(data)


    state: State = State()
    state.locations = {"Arrivals": "loc_1", "Server": "loc_1"}
    state.globalVars = {"queue": 1, "served_customer": True}
    state.globalTime = 0.0
    state.autoVars = {"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 0, "c": 0}}

    STASim = STASimulator(model)
    print(state.globalVars)

    STASim.restart_transient_variables(state)
    print(state.globalVars)

    assert state.globalVars["served_customer"] == False
    assert state.globalVars["queue"] == 1
    

    pass