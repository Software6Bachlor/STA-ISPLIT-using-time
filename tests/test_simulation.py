def test_restartTransientVariables_resetsToInitialValue():
    from models.simulation import STASimulator, State
    from models.STA import Model, Literal
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

    assert state.globalVars["served_customer"] == Literal(value=False)

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


def test_calculateTimeUntilValid_orOperatorUnionButWithGap1():
    from models.STA import Edge, BinaryExpression, Literal, VariableReference
    from models.state import State
    from mocks import model_1 as model
    from models.simulation import STASimulator


    model.automata[0].edges[0] = None
    model.automata[0].edges[1].guard = BinaryExpression(
        op="∨", 
        left=BinaryExpression(op="<", left=VariableReference("c"), right=Literal(1)), 
        right=BinaryExpression(op="<", left=Literal("2"), right=VariableReference("c"))
        )
    STASim = STASimulator(model)
    
    edge: Edge = Edge("loc_1", model.automata[0].edges[1].guard, model.automata[0].edges[1].destinations)
    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 1, "c": 0}})
    
    interval = STASim.calculateTimeUntilEdgeBecomesValid(edge.guard, state, model.automata[0])
    print(interval)
    assert interval == 0


def test_calculateTimeUntilValid_orOperatorUnionButWithGap2():
    from models.STA import Edge, BinaryExpression, Literal, VariableReference
    from mocks import model_1 as model
    from models.state import State
    from models.simulation import STASimulator

    model.automata[0].edges[0] = None
    model.automata[0].edges[1].guard = BinaryExpression(
        op="∨", 
        left=BinaryExpression(op="<", left=VariableReference("c"), right=Literal(2)), 
        right=BinaryExpression(op="<", left=VariableReference("c"), right=Literal("3"))
        )
    STASim = STASimulator(model)
    
    edge: Edge = Edge("loc_1", model.automata[0].edges[1].guard, model.automata[0].edges[1].destinations)
    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 0, "c": 0}})
    
    interval = STASim.calculateTimeUntilEdgeBecomesValid(edge.guard, state, model.automata[0])
    assert interval == 0


def test_calculateTimeUntilValid_orOperatorUnionWithVariableRef():
    from models.STA import Edge, BinaryExpression, Literal, VariableReference
    from mocks import model_1 as model
    from models.state import State
    from models.simulation import STASimulator

    model.automata[0].edges[0] = None
    model.automata[0].edges[1].guard = BinaryExpression(
        op="∨", 
        left=BinaryExpression(op=">", left=VariableReference("c"), right=VariableReference("x")), 
        right=BinaryExpression(op="<", left=VariableReference("c"), right=Literal("1"))
        )
    STASim = STASimulator(model)
    
    edge: Edge = Edge("loc_1", model.automata[0].edges[1].guard, model.automata[0].edges[1].destinations)
    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 5, "c": 0}, "Server": {"x": 10, "c": 0}})
    
    interval = STASim.calculateTimeUntilEdgeBecomesValid(edge.guard, state, model.automata[0])
    assert interval == 0

def test_calculateTimeUntilValid_orOperatorUnionWithLiterals():
    from models.STA import Edge, BinaryExpression, Literal, VariableReference
    from models.state import State
    from mocks import model_1 as model
    from models.simulation import STASimulator

    model.automata[0].edges[0] = None
    model.automata[0].edges[1].guard = BinaryExpression(
        op="∨", 
        left=BinaryExpression(op=">", left=Literal("1"), right=Literal("0")), 
        right=BinaryExpression(op="==", left=Literal("2"), right=Literal("2"))
        )
    STASim = STASimulator(model)
    
    edge: Edge = Edge("loc_1", model.automata[0].edges[1].guard, model.automata[0].edges[1].destinations)
    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 5, "c": 0}, "Server": {"x": 10, "c": 0}})
    
    interval = STASim.calculateTimeUntilEdgeBecomesValid(edge.guard, state, model.automata[0])
    assert interval == 0




def test_calculateTimeUntilValid_andOperator():
    from models.STA import Edge, BinaryExpression, Literal, VariableReference
    from models.state import State
    from mocks import model_1 as model
    from models.simulation import STASimulator

    model.automata[0].edges[0] = None
    model.automata[0].edges[1].guard = BinaryExpression(
        op="∧", 
        left=BinaryExpression(op="<", left=VariableReference("c"), right=Literal(4)), 
        right=BinaryExpression(op="<", left=Literal("3"), right=VariableReference("c"))
        )
    STASim = STASimulator(model)
    
    edge: Edge = Edge("loc_1", model.automata[0].edges[1].guard, model.automata[0].edges[1].destinations)
    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 1, "c": 0}})
    
    interval = STASim.calculateTimeUntilEdgeBecomesValid(edge.guard, state, model.automata[0])
    print(interval)
    assert interval == 3



def test_calculateTimeUntilValid_andOperatorMoreComplex():
    from models.STA import Edge, BinaryExpression, Literal, VariableReference
    from models.state import State
    from mocks import model_1 as model
    from models.simulation import STASimulator

    model.automata[0].edges[0] = None

    bin = BinaryExpression(
        op="∨", 
        left=BinaryExpression(op="<", left=VariableReference("c"), right=Literal(1)), 
        right=BinaryExpression(
            op="∧",
            left=BinaryExpression(op="<", left=Literal("2"), right=VariableReference("c")),
            right=BinaryExpression(op="<", left=VariableReference("c"), right=Literal("3"))
            )
        )

    model.automata[0].edges[1].guard = BinaryExpression(
        op="∧", 
        left=bin, 
        right=bin
    )
    STASim = STASimulator(model)
    
    edge: Edge = Edge("loc_1", model.automata[0].edges[1].guard, model.automata[0].edges[1].destinations)
    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 1, "c": 0}})
    
    interval = STASim.calculateTimeUntilEdgeBecomesValid(edge.guard, state, model.automata[0])
    print(interval)
    assert interval == 0




def test_solve_guard_orOperatorUnionButWithGap1():
    from models.STA import Edge, BinaryExpression, Literal, VariableReference
    from models.state import State
    from mocks import model_1 as model
    from models.interval import Interval
    from models.simulation import STASimulator

    model.automata[0].edges[0] = None
    model.automata[0].edges[1].guard = BinaryExpression(
        op="∨", 
        left=BinaryExpression(op="<", left=VariableReference("c"), right=Literal(1)), 
        right=BinaryExpression(op="<", left=Literal("2"), right=VariableReference("c"))
        )
    STASim = STASimulator(model)
    edge: Edge = Edge("loc_1", model.automata[0].edges[1].guard, model.automata[0].edges[1].destinations)
    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 1, "c": 0}})
    
    interval = STASim.solve_guard(edge.guard, state, model.automata[0])
    print(interval)
    assert interval == [Interval(0,1, True, False), Interval(2, float("inf"), False, True)]



def test_solve_guard_orOperatorUnionButWithGap2():
    from models.STA import Edge, BinaryExpression, Literal, VariableReference
    from mocks import model_1 as model
    from models.state import State
    from models.simulation import STASimulator
    from models.interval import Interval

    model.automata[0].edges[0] = None
    model.automata[0].edges[1].guard = BinaryExpression(
        op="∨", 
        left=BinaryExpression(op="≤", left=VariableReference("c"), right=Literal(2)), 
        right=BinaryExpression(op="≤", left=VariableReference("c"), right=Literal(3))
        )
    STASim = STASimulator(model)
    
    edge: Edge = Edge("loc_1", model.automata[0].edges[1].guard, model.automata[0].edges[1].destinations)
    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 0, "c": 0}})
    
    interval = STASim.solve_guard(edge.guard, state, model.automata[0])
    assert interval == [Interval(0, 3, True, True)]


def test_solve_guard_orOperatorUnionWithVariableRef():
    from models.STA import Edge, BinaryExpression, Literal, VariableReference
    from mocks import model_1 as model
    from models.state import State
    from models.interval import Interval
    from models.simulation import STASimulator
    model.automata[0].edges[0] = None
    model.automata[0].edges[1].guard = BinaryExpression(
        op="∨", 
        left=BinaryExpression(op=">", left=VariableReference("c"), right=VariableReference("x")), 
        right=BinaryExpression(op="<", left=VariableReference("c"), right=Literal("1"))
        )
    STASim = STASimulator(model)
    
    edge: Edge = Edge("loc_1", model.automata[0].edges[1].guard, model.automata[0].edges[1].destinations)
    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 5, "c": 0}, "Server": {"x": 10, "c": 0}})
    
    interval = STASim.solve_guard(edge.guard, state, model.automata[0])
    assert interval == [Interval(0, 1, True, False), Interval(5, float("inf"), False, True)]

def test_solve_guard_orOperatorUnionWithLiterals():
    from models.STA import Edge, BinaryExpression, Literal, VariableReference
    from models.interval import Interval
    from models.state import State
    from mocks import model_1 as model
    from models.simulation import STASimulator

    model.automata[0].edges[0] = None
    model.automata[0].edges[1].guard = BinaryExpression(
        op="∨", 
        left=BinaryExpression(op=">", left=Literal("1"), right=Literal("0")), 
        right=BinaryExpression(op="==", left=Literal("2"), right=Literal("2"))
        )
    STASim = STASimulator(model)
    
    edge: Edge = Edge("loc_1", model.automata[0].edges[1].guard, model.automata[0].edges[1].destinations)
    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 5, "c": 0}, "Server": {"x": 10, "c": 0}})
    
    interval = STASim.solve_guard(edge.guard, state, model.automata[0])
    assert interval == [Interval(0, float("inf"), True, True)]




def test_solve_guard_andOperator():
    from models.STA import Edge, BinaryExpression, Literal, VariableReference
    from models.state import State
    from mocks import model_1 as model
    from models.interval import Interval
    from models.simulation import STASimulator
    model.automata[0].edges[0] = None
    model.automata[0].edges[1].guard = BinaryExpression(
        op="∧", 
        left=BinaryExpression(op="<", left=VariableReference("c"), right=Literal(4)), 
        right=BinaryExpression(op="<", left=Literal("3"), right=VariableReference("c"))
        )
    STASim = STASimulator(model)
    
    edge: Edge = Edge("loc_1", model.automata[0].edges[1].guard, model.automata[0].edges[1].destinations)
    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 1, "c": 0}})
    
    interval = STASim.solve_guard(edge.guard, state, model.automata[0])
    print(interval)
    assert interval == [Interval(3, 4, False, False)]



def test_solve_guard_andOperatorMoreComplex():
    from models.STA import Edge, BinaryExpression, Literal, VariableReference
    from models.state import State
    from models.interval import Interval
    from mocks import model_1 as model
    from models.simulation import STASimulator

    model.automata[0].edges[0] = None

    bin = BinaryExpression(
        op="∨", 
        left=BinaryExpression(op="<", left=VariableReference("c"), right=Literal(1)), 
        right=BinaryExpression(
            op="∧",
            left=BinaryExpression(op="<", left=Literal("2"), right=VariableReference("c")),
            right=BinaryExpression(op="<", left=VariableReference("c"), right=Literal("3"))
            )
        )

    model.automata[0].edges[1].guard = BinaryExpression(
        op="∧", 
        left=bin, 
        right=bin
    )
    STASim = STASimulator(model)
    
    edge: Edge = Edge("loc_1", model.automata[0].edges[1].guard, model.automata[0].edges[1].destinations)
    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 1, "c": 0}})
    
    interval = STASim.solve_guard(edge.guard, state, model.automata[0])


    assert interval == [Interval(0, 1, True, False), Interval(2, 3, False, False)]


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



def test_getNextValidEdges_fromInitalStateReturnsCorrectEdgeWhenOnlyOneEdge():
    from models.STA import Model, Edge
    from parser import parseModel
    from loader import loadData
    from utilities.get_initial_state import get_initial_state
    from models.state import State
    from models.simulation import STASimulator

    data = loadData("tests//testdata//manufacturing-sta.jani")  
    model: Model = parseModel(data)

    STASim: STASimulator = STASimulator(model)

    init_state: State = get_initial_state(model)

    edges: list[tuple[Edge, float, str]] = STASim.getNextValidEdges(init_state)

    assert len(edges) == 1
    assert edges[0][0].destinations[0].location == "loc_7"
    assert edges[0][1] < 5
    assert edges[0][1] > 2
    assert edges[0][2] == "Idle"

def test_intervalsNegated_returnsNegatedWhenNo0():
    from utilities.intervals_negated import intervals_negated
    from models.interval import Interval

    assert intervals_negated([Interval(1, 2, False, True)]) == [Interval(0, 1, True, True), Interval(2, float("inf"), False, True)]

def test_intervalsNegated_returnsNegatedWhen0():
    from utilities.intervals_negated import intervals_negated
    from models.interval import Interval
    assert intervals_negated([Interval(0, 2, True, True)]) == [Interval(2, float("inf"), False, True)]


def test_intervalsNegated_returnsNegatedWhenInfand0():
    from utilities.intervals_negated import intervals_negated
    from models.interval import Interval
    assert intervals_negated([Interval(0, float("inf"), True, True)]) == None

def test_intervalsNegated_returnsNegatedWhenInf():
    from utilities.intervals_negated import intervals_negated
    from models.interval import Interval
    
    assert intervals_negated([Interval(1, float("inf"), False, True)]) == [Interval(0, 1, True, True)]


def test_handlePendingAssignments_UpdatesAutoVarsWhenLocalVarInPendingAssignments():
    from models.simulation import STASimulator, State
    from models.STA import Model, Literal, Assignment
    from parser import parseModel
    from loader import loadData
    

    data = loadData("tests//testdata//ModestSTA.jani")  
    model: Model = parseModel(data)
    simulator = STASimulator(model)

    oldState: State = State(locations={"Arrivals": "loc_2", "Server": "loc_1"},
                        globalVars={"queue": 1, "served_customer": False},
                        autoVars={"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 0, "c": 0}},
                        pendingAssignments=[Assignment(ref="x", value=Literal(value=5.0))],
                        recentAutomaton="Arrivals"
                                    )
    newState = oldState.clone()


    simulator.handlePendingAssignments(oldState, newState)


    assert newState.autoVars["Arrivals"]["x"] == 5.0


def test_handlePendingAssignments_expression():
    from models.STA import Model, Assignment, Literal
    from parser import parseModel
    from loader import loadData
    from models.state import State
    from models.simulation import STASimulator

    data = loadData("tests//testdata//ModestSTA.jani")

    model: Model = parseModel(data)
    simulator = STASimulator(model)

    oldState: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         recentAutomaton="Arrivals",
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 0, "c": 0}},
                         pendingAssignments=[Assignment(ref="served_customer", value=Literal(value=False))])
    
    newState = oldState.clone()

    simulator.handlePendingAssignments(oldState, newState)

    assert newState.globalVars["served_customer"] == False

def test_handlePendingAssignments_distribution():
    from models.STA import Model, Assignment, Literal, Distribution
    from parser import parseModel
    from loader import loadData
    from models.state import State
    from models.simulation import STASimulator

    data = loadData("tests//testdata//manufacturing-sta.jani")

    model: Model = parseModel(data)
    simulator = STASimulator(model)

    oldState: State = State(locations={"Idle": "loc_1"},
                         recentAutomaton="Idle",
                         globalVars={},
                         autoVars={"Idle": {"x": 0, "c": 0}},
                         pendingAssignments=[Assignment(ref="x", value=Distribution(type="uniform", args=[Literal(2), Literal(5)]))])
    newState = oldState.clone()


    simulator.handlePendingAssignments(oldState, newState)

    assert newState.autoVars["Idle"]["x"] < 5
    assert newState.autoVars["Idle"]["x"] > 2



