def test_restartTransientVariables_resetsToInitialValue():
    from models.simulation import STASimulator, State
    from models.STA import Model
    from parser import parseModel
    from loader import loadData

    data = loadData("tests//testdata//ModestSTA.jani")  
    model: Model = parseModel(data)


    state: State = State()
    state.locations = {"Arrivals": "loc_1", "Server": "loc_1"}
    state.globalVars = {"queue": 1, "served_customer": True}
    state.globalTime = 0.0
    state.autoVars = {"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 0, "c": 0}}

    STASim = STASimulator(model)
    print(state.globalVars)

    STASim.restartTransientVariables(state)
    print(state.globalVars)

    assert state.globalVars["served_customer"] == False
    

    pass

def test_restartTransientVariables_doesNotresetIfNotTransient():
    from models.simulation import STASimulator, State
    from models.STA import Model
    from parser import parseModel
    from loader import loadData

    data = loadData("tests//testdata//ModestSTA.jani")  
    model: Model = parseModel(data)


    state: State = State()
    state.locations = {"Arrivals": "loc_1", "Server": "loc_1"}
    state.globalVars = {"queue": 1, "served_customer": True}
    state.globalTime = 0.0
    state.autoVars = {"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 0, "c": 0}}

    STASim = STASimulator(model)
    print(state.globalVars)

    STASim.restartTransientVariables(state)
    print(state.globalVars)

    assert state.globalVars["queue"] == 1
    

    pass


# def test_fastForwardTimeAdvancesClocks():
#     from models.simulation import STASimulator, State
#     from models.STA import Model
#     from parser import parseModel
#     from loader import loadData

#     data = loadData("tests//testdata//ModestSTA.jani")  
#     model: Model = parseModel(data)

#     state: State = State()
#     state.locations = {"Arrivals": "loc_1", "Server": "loc_1"} 
#     state.globalVars = {"queue": 1, "served_customer": False}
#     state.globalTime = 10.0
#     state.autoVars = {
#         "Arrivals": {"x": 5.0, "c": 1.0}, 
#         "Server": {"x": 3.0, "c": 2.0}
#     }

#     STASim = STASimulator(model)
#     newState = STASim.fastForwardTime(state) 


#     assert newState.globalTime == 11.0
#     assert newState.autoVars["Arrivals"]["c"] == 2.0  
#     assert newState.autoVars["Server"]["c"] == 3.0   

def test_calculateEdgeTimeLeap():
    from models.simulation import STASimulator, State
    from models.STA import Model
    from parser import parseModel
    from loader import loadData

    data = loadData("tests//testdata//ModestSTA.jani")  
    model: Model = parseModel(data)

    state: State = State()
    state.locations = {"Arrivals": "loc_1", "Server": "loc_1"} 
    state.globalVars = {"queue": 1, "served_customer": False}
    state.globalTime = 10.0
    state.autoVars = {
        "Arrivals": {"x": 5.0, "c": 1.0}, 
        "Server": {"x": 3.0, "c": 2.0}
    }

    STASim: STASimulator = STASimulator(model)
    STASim.calculateEdgeTimeLeap("1+1", state, model.automata[0])


    assert 1==2