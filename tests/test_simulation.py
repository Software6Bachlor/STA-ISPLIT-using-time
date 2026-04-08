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



def test_getNextValidEdges_returnsCorrectStateWhenOnlyOneEdge():
    from models.simulation import STASimulator
    from models.STA import Model, Edge
    from parser import parseModel
    from models.state import State
    from loader import loadData
    from utilities.initial_state import get_initial_state

    data = loadData("tests//testdata//manufacturing-sta.jani")  
    model: Model = parseModel(data)

    initState: State = get_initial_state(model)
    print(initState.autoVars)
    STASim :STASimulator = STASimulator(model)

    nextValidEdges: list[tuple[Edge, float]] = STASim.getNextValidEdges(initState)
    
    print(len(nextValidEdges))
    assert len(nextValidEdges) == 1


def test_getNextValidEdges_returnsCorrectEdgeWhenOnlyOneValidEdge():
    import random
    from models.simulation import STASimulator, State
    from models.STA import Model, Edge
    from parser import parseModel
    from loader import loadData
    from models.state import State

    data = loadData("tests//testdata//manufacturing-sta.jani")  
    model: Model = parseModel(data)

    # build the autoVars dictionary from the parsed model (intial values)
    dynamic_auto_vars = {}
    
    for automaton in model.automata:
        dynamic_auto_vars[automaton.name] = {}
        for var in automaton.variables:
            init_val = var.initial_value
            
            # Check if the initial value is a distribution. only uniform hardcoded as only this in the model.
            if isinstance(init_val, dict) and 'distribution' in init_val:
                if init_val['distribution'] == 'Uniform':
                    lower_bound = init_val['args'][0]
                    upper_bound = init_val['args'][1]
                    # Sample a float between the bounds
                    sampled_val = random.uniform(lower_bound, upper_bound)
                    dynamic_auto_vars[automaton.name][var.name] = sampled_val
                
            else:
                # Normal constant initial values (like 0)
                dynamic_auto_vars[automaton.name][var.name] = float(init_val)

    # 2. Pass the dynamically generated dictionary into the State
    state: State = State(
        locations={"Idle": "loc_1"},  # Assuming 'Idle' is model.automata[0].name
        globalVars={"acycle": 0.0, "uptime": 0.0, "failure": False},
        autoVars=dynamic_auto_vars
    )
    STASim = STASimulator(model)

    nextEdges: list[tuple[Edge, float]] = STASim.getNextValidEdges(state)
    print(state.autoVars)

    #Next state vald will always be loc_7.
    assert len(nextEdges) == 1
    assert nextEdges[0][0].destinations[0].location == "loc_7"

    
# def test_getNextValidEdge_returnCorrectEdgeWhenTwoValidEdges():
#     import random
#     from models.simulation import STASimulator, State
#     from models.STA import Model, Edge
#     from parser import parseModel
#     from loader import loadData

#     data = loadData("tests//testdata//manufacturing-sta.jani")  
#     model: Model = parseModel(data)

    
#     STASim = STASimulator(model)

#     nextEdges: list[tuple[Edge, float]] = STASim.getNextValidEdges(state)
#     print(state.autoVars)

#     #Next state vald will always be loc_7.
#     assert len(nextEdges) == 1
#     assert nextEdges[0][0].destinations[0].location == "loc_7"



def test_calculateTimeUntilValid_orOperatorUnionButWithGap1():
    from models.STA import Edge, BinaryExpression, Literal, VariableReference
    from models.state import State
    from mocks import model_1 as model

    model.automata[0].edges[0] = None
    model.automata[0].edges[1].guard = BinaryExpression(
        op="∨", 
        left=BinaryExpression(op="<", left=VariableReference("c"), right=Literal(1)), 
        right=BinaryExpression(op="<", left=Literal("2"), right=VariableReference("c"))
        )
    
    edge: Edge = Edge("loc_1", model.automata[0].edges[1].guard, model.automata[0].edges[1].destinations)
    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 1, "c": 0}})
    
    interval = edge.calculateTimeUntilValid(edge.guard, state, model.automata[0])
    print(interval)
    assert interval == 0


def test_calculateTimeUntilValid_orOperatorUnionButWithGap2():
    from models.STA import Edge, BinaryExpression, Literal, VariableReference
    from mocks import model_1 as model
    from models.state import State

    model.automata[0].edges[0] = None
    model.automata[0].edges[1].guard = BinaryExpression(
        op="∨", 
        left=BinaryExpression(op="<", left=VariableReference("c"), right=Literal(2)), 
        right=BinaryExpression(op="<", left=VariableReference("c"), right=Literal("3"))
        )
    
    edge: Edge = Edge("loc_1", model.automata[0].edges[1].guard, model.automata[0].edges[1].destinations)
    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 0, "c": 0}})
    
    interval = edge.calculateTimeUntilValid(edge.guard, state, model.automata[0])
    assert interval == 0


def test_calculateTimeUntilValid_orOperatorUnionWithVariableRef():
    from models.STA import Edge, BinaryExpression, Literal, VariableReference
    from mocks import model_1 as model
    from models.state import State

    model.automata[0].edges[0] = None
    model.automata[0].edges[1].guard = BinaryExpression(
        op="∨", 
        left=BinaryExpression(op=">", left=VariableReference("c"), right=VariableReference("x")), 
        right=BinaryExpression(op="<", left=VariableReference("c"), right=Literal("1"))
        )
    
    edge: Edge = Edge("loc_1", model.automata[0].edges[1].guard, model.automata[0].edges[1].destinations)
    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 5, "c": 0}, "Server": {"x": 10, "c": 0}})
    
    interval = edge.calculateTimeUntilValid(edge.guard, state, model.automata[0])
    assert interval == 0

def test_calculateTimeUntilValid_orOperatorUnionWithLiterals():
    from models.STA import Edge, BinaryExpression, Literal, VariableReference
    from models.state import State
    from mocks import model_1 as model

    model.automata[0].edges[0] = None
    model.automata[0].edges[1].guard = BinaryExpression(
        op="∨", 
        left=BinaryExpression(op=">", left=Literal("1"), right=Literal("0")), 
        right=BinaryExpression(op="==", left=Literal("2"), right=Literal("2"))
        )
    
    edge: Edge = Edge("loc_1", model.automata[0].edges[1].guard, model.automata[0].edges[1].destinations)
    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 5, "c": 0}, "Server": {"x": 10, "c": 0}})
    
    interval = edge.calculateTimeUntilValid(edge.guard, state, model.automata[0])
    assert interval == 0




def test_calculateTimeUntilValid_andOperator():
    from models.STA import Edge, BinaryExpression, Literal, VariableReference
    from models.state import State
    from mocks import model_1 as model

    model.automata[0].edges[0] = None
    model.automata[0].edges[1].guard = BinaryExpression(
        op="∧", 
        left=BinaryExpression(op="<", left=VariableReference("c"), right=Literal(4)), 
        right=BinaryExpression(op="<", left=Literal("3"), right=VariableReference("c"))
        )
    
    edge: Edge = Edge("loc_1", model.automata[0].edges[1].guard, model.automata[0].edges[1].destinations)
    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 1, "c": 0}})
    
    interval = edge.calculateTimeUntilValid(edge.guard, state, model.automata[0])
    print(interval)
    assert interval == 3



def test_calculateTimeUntilValid_andOperatorMoreComplex():
    from models.STA import Edge, BinaryExpression, Literal, VariableReference
    from models.state import State
    from mocks import model_1 as model

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
    
    edge: Edge = Edge("loc_1", model.automata[0].edges[1].guard, model.automata[0].edges[1].destinations)
    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 1, "c": 0}})
    
    interval = edge.calculateTimeUntilValid(edge.guard, state, model.automata[0])
    print(interval)
    assert interval == 0




def test_solve_guard_orOperatorUnionButWithGap1():
    from models.STA import Edge, BinaryExpression, Literal, VariableReference
    from models.state import State
    from mocks import model_1 as model

    model.automata[0].edges[0] = None
    model.automata[0].edges[1].guard = BinaryExpression(
        op="∨", 
        left=BinaryExpression(op="<", left=VariableReference("c"), right=Literal(1)), 
        right=BinaryExpression(op="<", left=Literal("2"), right=VariableReference("c"))
        )
    
    edge: Edge = Edge("loc_1", model.automata[0].edges[1].guard, model.automata[0].edges[1].destinations)
    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 1, "c": 0}})
    
    interval = edge.solve_guard(edge.guard, state, model.automata[0])
    print(interval)
    assert interval == [(0,1), (2, float("inf"))]



def test_solve_guard_orOperatorUnionButWithGap2():
    from models.STA import Edge, BinaryExpression, Literal, VariableReference
    from mocks import model_1 as model
    from models.state import State

    model.automata[0].edges[0] = None
    model.automata[0].edges[1].guard = BinaryExpression(
        op="∨", 
        left=BinaryExpression(op="<", left=VariableReference("c"), right=Literal(2)), 
        right=BinaryExpression(op="<", left=VariableReference("c"), right=Literal("3"))
        )
    
    edge: Edge = Edge("loc_1", model.automata[0].edges[1].guard, model.automata[0].edges[1].destinations)
    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 0, "c": 0}})
    
    interval = edge.solve_guard(edge.guard, state, model.automata[0])
    assert interval == [(0,3)]


def test_solve_guard_orOperatorUnionWithVariableRef():
    from models.STA import Edge, BinaryExpression, Literal, VariableReference
    from mocks import model_1 as model
    from models.state import State

    model.automata[0].edges[0] = None
    model.automata[0].edges[1].guard = BinaryExpression(
        op="∨", 
        left=BinaryExpression(op=">", left=VariableReference("c"), right=VariableReference("x")), 
        right=BinaryExpression(op="<", left=VariableReference("c"), right=Literal("1"))
        )
    
    edge: Edge = Edge("loc_1", model.automata[0].edges[1].guard, model.automata[0].edges[1].destinations)
    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 5, "c": 0}, "Server": {"x": 10, "c": 0}})
    
    interval = edge.solve_guard(edge.guard, state, model.automata[0])
    assert interval == [(0,1), (5,float("inf"))]

def test_solve_guard_orOperatorUnionWithLiterals():
    from models.STA import Edge, BinaryExpression, Literal, VariableReference
    from models.state import State
    from mocks import model_1 as model

    model.automata[0].edges[0] = None
    model.automata[0].edges[1].guard = BinaryExpression(
        op="∨", 
        left=BinaryExpression(op=">", left=Literal("1"), right=Literal("0")), 
        right=BinaryExpression(op="==", left=Literal("2"), right=Literal("2"))
        )
    
    edge: Edge = Edge("loc_1", model.automata[0].edges[1].guard, model.automata[0].edges[1].destinations)
    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 5, "c": 0}, "Server": {"x": 10, "c": 0}})
    
    interval = edge.solve_guard(edge.guard, state, model.automata[0])
    assert interval == [(0,float("inf"))]




def test_solve_guard_andOperator():
    from models.STA import Edge, BinaryExpression, Literal, VariableReference
    from models.state import State
    from mocks import model_1 as model

    model.automata[0].edges[0] = None
    model.automata[0].edges[1].guard = BinaryExpression(
        op="∧", 
        left=BinaryExpression(op="<", left=VariableReference("c"), right=Literal(4)), 
        right=BinaryExpression(op="<", left=Literal("3"), right=VariableReference("c"))
        )
    
    edge: Edge = Edge("loc_1", model.automata[0].edges[1].guard, model.automata[0].edges[1].destinations)
    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 1, "c": 0}})
    
    interval = edge.solve_guard(edge.guard, state, model.automata[0])
    print(interval)
    assert interval == [(3,4)]



def test_solve_guard_andOperatorMoreComplex():
    from models.STA import Edge, BinaryExpression, Literal, VariableReference
    from models.state import State
    from mocks import model_1 as model

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
    
    edge: Edge = Edge("loc_1", model.automata[0].edges[1].guard, model.automata[0].edges[1].destinations)
    state: State = State(locations={"Arrivals": "loc_1", "Server": "loc_1"},
                         globalVars={"queue": 0, "served_customer": True},
                         autoVars={"Arrivals": {"x": 0, "c": 0}, "Server": {"x": 1, "c": 0}})
    
    interval = edge.solve_guard(edge.guard, state, model.automata[0])
    print(interval)
    assert interval == [(0,1), (2,3)]
