def test_restartTransientVariables_resetsToInitialValue():
    from models.simulation import STASimulator, State
    from models.STA import Model
    from parser import parseModel
    from loader import loadData

    data = loadData("tests//testdata//ModestSTA.jani")  
    model: Model = parseModel(data)


    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                          globalVars={"queue": 1, "served_customer": True},
                          autoVars={"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 0, "c": 0}})

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


    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 1, "served_customer": True},
                         autoVars={"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 0, "c": 0}})

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














# def test_calculateEdgeTimeLeap_invalidVariables_returnsInfinity():
#     from models.simulation import STASimulator, State
#     from models.STA import Model
#     from parser import parseModel
#     from loader import loadData

#     data = loadData("tests//testdata//ModestSTA.jani")  
#     model: Model = parseModel(data)

#     state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
#                          globalVars={"queue": 1, "served_customer": False},
#                          autoVars={"Arrivals": {"x": 5.0, "c": 1.0}, "Server": {"x": 3.0, "c": 2.0}},
#                          globalTime= 10.0)
#     # queue is 1, so a guard requiring queue == 5 is FALSE
#     STASim = STASimulator(model)
    
#     # Test: Variables are false. Even if clock 'c' was met, the edge can't be taken.
#     # Expectation: Should return infinity (or -1/None, depending on your implementation).
#     leap = STASim.calculateEdgeTimeLeap("queue == 5", state, model.automata[0])
    
#     # Adjust float('inf') to whatever your function returns when an edge is impassable
#     #assert leap == float('inf'), f"Expected infinity for impassable guard, got {leap}"


# def test_calculateEdgeTimeLeap_validVariables_clockAlreadyMet_returnsZero():
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
#         "Arrivals": {"x": 5.0, "c": 1.0}, # Automaton 0 (Arrivals) clock 'c' is 1.0
#         "Server": {"x": 3.0, "c": 2.0}
#     }

#     STASim = STASimulator(model)
    
#     # Test: queue is 1 (True), and clock c is >= 1.0 (True)
#     # Expectation: Leap should be 0.0 because the edge is immediately available.
#     leap = STASim.calculateEdgeTimeLeap("queue == 1 && c >= 1.0", state, model.automata[0])
    
#     assert leap == 0.0, f"Expected 0.0 leap for immediately valid edge, got {leap}"


# def test_calculateEdgeTimeLeap_validVariables_clockInFuture_returnsLeap():
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
#         "Arrivals": {"x": 5.0, "c": 1.0}, # Clock 'c' is currently 1.0
#         "Server": {"x": 3.0, "c": 2.0}
#     }

#     STASim = STASimulator(model)
    
#     # Test: queue is 1 (True). Clock 'c' needs to be >= 4.0.
#     # Since 'c' is 1.0, it needs exactly 3.0 more time units.
#     # Expectation: Leap should be 3.0.
#     leap = STASim.calculateEdgeTimeLeap("queue == 1 && c >= 4.0", state, model.automata[0])
    
#     assert leap == 3.0, f"Expected a leap of 3.0, got {leap}"


def test_getEdgesWhichBecomesValidFirst_returnsEdge():
    from models.simulation import STASimulator, State
    from models.STA import Model, Edge
    from parser import parseModel
    from loader import loadData

    data = loadData("tests//testdata//ModestSTA.jani")  
    model: Model = parseModel(data)

    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 0, "served_customer": False},
                         autoVars={"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 0, "c": 0}})

    STASim = STASimulator(model)

    nextEdges: list[Edge] = STASim.getNextValidEdges(state)

    assert (len(nextEdges) == 2)



    