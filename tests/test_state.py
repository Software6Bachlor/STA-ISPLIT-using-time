def test_handlePendingAssignments_UpdatesAutoVarsWhenLocalVarInPendingAssignments():
    from models.simulation import STASimulator, State
    from models.STA import Model, Literal, Assignment
    from parser import parseModel
    from loader import loadData
    

    data = loadData("tests//testdata//ModestSTA.jani")  
    model: Model = parseModel(data)

    state: State = State(locations={"Arrivals": "loc_2", "Server": "loc_1"},
                        globalVars={"queue": 1, "served_customer": False},
                        autoVars={"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 0, "c": 0}},
                        pendingAssignments=[Assignment(ref="x", value=Literal(value=5.0))],
                        recentAutomaton="Arrivals"
                                    )

    state.handlePendingAssignments()


    assert state.autoVars["Arrivals"]["x"] == 5.0


def test_handlePendingAssignments_expression():
    from models.STA import Model, Assignment, Literal
    from parser import parseModel
    from loader import loadData
    from models.state import State
    from models.simulation import STASimulator

    data = loadData("tests//testdata//ModestSTA.jani")

    model: Model = parseModel(data)

    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         recentAutomaton="Arrivals",
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 0, "c": 0}},
                         pendingAssignments=[Assignment(ref="served_customer", value=Literal(value=False))])

    state.handlePendingAssignments()

    assert state.globalVars["served_customer"] == False

def test_handlePendingAssignments_distribution():
    from models.STA import Model, Assignment, Literal, Distribution
    from parser import parseModel
    from loader import loadData
    from models.state import State
    from models.simulation import STASimulator

    data = loadData("tests//testdata//manufacturing-sta.jani")

    model: Model = parseModel(data)

    state: State = State(locations={"Idle": "loc_1"},
                         recentAutomaton="Idle",
                         globalVars={},
                         autoVars={"Idle": {"x": 0, "c": 0}},
                         pendingAssignments=[Assignment(ref="x", value=Distribution(type="uniform", args=[Literal(2), Literal(5)]))])

    state.handlePendingAssignments()

    assert state.autoVars["Idle"]["x"] < 5
    assert state.autoVars["Idle"]["x"] > 2