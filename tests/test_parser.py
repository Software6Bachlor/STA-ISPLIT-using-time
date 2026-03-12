from importlib.metadata import Distribution


def test_parse_model():
    from parser import parse_model
    
    # Arrange
    data = {
        "name": "test_model",
        "jani-version": "1.0",
        "type": "STA",
        "features": ["feature1", "feature2"],
        "variables": [
            {"name": "x", "type": "int"},
            {"name": "y", "type": "bool"}
        ],
        "constants": [
            {"name": "c1", "type": "int", "value": 10}
        ]
    }

    # Act
    model = parse_model(data)

    # Assert
    assert model.name == "test_model"
    assert model.jani_version == "1.0"
    assert model.type == "STA"
    assert model.features == ["feature1", "feature2"]

def test_parse_constants():
    from parser import parse_constants
    
    # Arrange
    data = [
        {"name": "c1", "type": "int"},
        {"name": "c2", "type": "bool"}
    ]

    # Act
    constants = parse_constants(data)

    # Assert
    assert len(constants) == 2
    assert constants[0].name == "c1"
    assert constants[0].type == "int"
    assert constants[1].name == "c2"
    assert constants[1].type == "bool"

def test_parse_variables():
    from parser import parse_variables
    from models.STA import VariableType
    
    # Arrange
    data = [
        {"name": "x", "type": "int", "initial-value": 0},
        {"name": "y", "type": "bool"},
        {"name": "z", "type": {"kind": "int", "base": 10, "lower-bound": 0, "upper-bound": 100}}
    ]

    # Act
    variables = parse_variables(data)

    # Assert
    assert len(variables) == 3
    assert variables[0].name == "x"
    assert variables[0].type == "int"
    assert variables[0].initial_value == 0
    assert variables[1].name == "y"
    assert variables[1].type == "bool"
    assert variables[1].initial_value is None
    assert variables[2].name == "z"
    assert isinstance(variables[2].type, VariableType)
    assert variables[2].type.kind == "int"
    assert variables[2].type.base == 10
    assert variables[2].type.lower_bound == 0
    assert variables[2].type.upper_bound == 100

def test_parse_property_expression_Pmax_filter():
    from parser import parse_property_expression
    from models.STA import BinaryExpression, PropertyExpression
    
    # Arrange
    data = {
    "op": "filter",
    "fun": "max",
    "values": {
        "op": "Pmax",
        "exp": {
            "op": "F",
            "exp": {"op": "=", "left": "queue", "right": 5},
            "time-bounds": {"upper": "TIME_BOUND"}
        }
    },
    "states": {"op": "initial"}
}

    # Act
    prop_expr = parse_property_expression(data)

    # Assert
    assert isinstance(prop_expr, PropertyExpression)
    assert prop_expr.op == "filter"
    assert prop_expr.operands["fun"] == "max"
    
    values = prop_expr.operands["values"]
    assert isinstance(values, PropertyExpression)
    assert values.op == "Pmax"
    
    f_expr = values.operands["exp"]
    assert isinstance(f_expr, PropertyExpression)
    assert f_expr.op == "F"
    
    state_expr = f_expr.operands["exp"]
    assert isinstance(state_expr, BinaryExpression)
    assert state_expr.op == "="

    

def test_parse_properties():
    from parser import parse_properties
    
    # Arrange
    data = [
        {
            "name": "p1",
            "expression": {
                "op": "op1",
                "fun": "fun1",
                "values": {"v1": 1},
                "states": {"s1": "state1"}
            }
        },
        {
            "name": "p2",
            "expression": {
                "op": "op2",
                "fun": "fun2",
                "values": {"v2": 2},
                "states": {"s2": "state2"}
            }
        }
    ]

    # Act
    properties = parse_properties(data)

    # Assert
    assert len(properties) == 2
    assert properties[0].name == "p1"
    assert properties[0].expression.op == "op1"
    assert properties[0].expression.operands["fun"] == "fun1"

def test_parse_automata():
    from parser import parse_automata
    
    # Arrange
    data = [
        {
            "name": "a1",
            "locations": [],
            "initial_locations": []
        },
        {
            "name": "a2",
            "locations": [],
            "initial_locations": []
        }
    ]

    # Act
    automata = parse_automata(data)

    # Assert
    assert len(automata) == 2
    assert automata[0].name == "a1"
    assert automata[1].name == "a2"

def test_parse_locations():
    from parser import parse_locations
    
    # Arrange
    data = [
        {"name": "loc1", "time-progress": {"exp": {"op": "op1", "left": {"value": 1}, "right": {"value": 2}}}},
        {"name": "loc2", "time-progress": {"exp": {"op": "op2", "left": {"value": 3}, "right": {"value": 4}}}}
    ]

    # Act
    locations = parse_locations(data)

    # Assert
    assert len(locations) == 2
    assert locations[0].name == "loc1"
    assert locations[0].timeProgress.op == "op1"
    assert locations[1].name == "loc2"
    assert locations[1].timeProgress.op == "op2"

def test_parse_expression_literal():
    from parser import parse_expression
    
    # Arrange
    literal_int = 5
    literal_bool = True
    literal_float = 0.5

    # Act
    expression_int = parse_expression(literal_int)
    expression_bool = parse_expression(literal_bool)
    expression_float = parse_expression(literal_float)

    # Assert
    assert expression_int.value == 5
    assert expression_bool.value == True
    assert expression_float.value == 0.5

def test_parse_expression_variable_reference():
    from parser import parse_expression
    
    # Arrange
    variable_ref = "queue"

    # Act
    expression = parse_expression(variable_ref)

    # Assert
    assert expression.name == "queue"

def test_parse_expression_binary_literals():
    from parser import parse_expression
    
    # Arrange
    data = {"op": "=", "left": "queue", "right": 5}

    # Act
    expression = parse_expression(data)

    # Assert
    assert expression.op == "="
    assert expression.left.name == "queue"
    assert expression.right.value == 5

def test_parse_expression_binary_nested_expressions():
    from parser import parse_expression
    
    # Arrange
    data = {
    "op": "∧",
    "left": {"op": "≥", "left": "c", "right": "x"},
    "right": {"op": "<", "left": "queue", "right": 5}
}

    # Act
    expression = parse_expression(data)

    # Assert
    assert expression.op == "∧"
    assert expression.left.op == "≥"
    assert expression.left.left.name == "c"
    assert expression.left.right.name == "x"
    assert expression.right.op == "<"
    assert expression.right.left.name == "queue"
    assert expression.right.right.value == 5

def test_parse_expression_if_then_else():
    from parser import parse_expression
    
    # Arrange
    data = {"op": "ite", "if": "served_customer", "then": 1, "else": 0}

    # Act
    expression = parse_expression(data)

    # Assert
    assert expression.condition.name == "served_customer"
    assert expression.then.value == 1
    assert expression.else_.value == 0

def test_parse_edges_simple():
    from parser import parse_edges
    
    # Arrange
    data = [{
    "location": "loc_1",
    "guard": {
        "exp": {
            "op": "∧",
            "left": {"op": "≥", "left": "c", "right": "x"},
            "right": {"op": "<", "left": "queue", "right": 5}
        }
    },
    "destinations": [
        {
            "location": "loc_2",
            "assignments": [
                {"ref": "queue", "value": {"op": "+", "left": "queue", "right": 1}},
                {"ref": "c", "value": 0}
            ]
        }
    ]
}]

    # Act
    edges = parse_edges(data)

    # Assert
    assert len(edges) == 1
    edge = edges[0]
    assert edge.location == "loc_1"
    assert edge.guard.op == "∧"
    assert edge.guard.left.left.name == "c"
    assert edge.guard.right.right.value == 5
    assert len(edge.destinations) == 1
    dest = edge.destinations[0]
    assert dest.location == "loc_2"
    assert dest.assignments[0].ref == "queue"
    assert dest.assignments[0].value.op == "+"
    assert dest.assignments[0].value.left.name == "queue"
    assert dest.assignments[0].value.right.value == 1
    assert dest.assignments[1].ref == "c"
    assert dest.assignments[1].value.value == 0

def test_parse_edges_with_distribution():
    from parser import parse_edges
    from models.STA import Distribution
    
    # Arrange
    data = [{
    "location": "loc_2",
    "guard": {
        "exp": {"op": ">", "left": "queue", "right": 0}
    },
    "destinations": [
        {
            "location": "loc_2",
            "assignments": [
                {"ref": "queue", "value": {"op": "-", "left": "queue", "right": 1}},
                {"ref": "c", "value": 0},
                {"ref": "x", "value": {"distribution": "Normal", "args": [10, 2]}}
            ]
        }
    ]
}]

    # Act
    edges = parse_edges(data)

    # Assert
    assert len(edges) == 1
    edge = edges[0]
    assert edge.location == "loc_2"
    assert edge.guard.op == ">"
    assert edge.guard.left.name == "queue"
    assert edge.guard.right.value == 0
    assert len(edge.destinations) == 1
    dest = edge.destinations[0]
    assert dest.location == "loc_2"
    assert dest.assignments[0].ref == "queue"
    assert dest.assignments[0].value.op == "-"
    assert dest.assignments[2].ref == "x"
    assert isinstance(dest.assignments[2].value, Distribution)
    assert dest.assignments[2].value.type == "Normal"
    assert dest.assignments[2].value.args[0].value == 10
    assert dest.assignments[2].value.args[1].value == 2

def test_parse_edges_with_no_guard():
    from parser import parse_edges
    
    # Arrange
    data = [{
    "location": "loc_1",
    "destinations": [
        {
            "location": "loc_2",
            "assignments": [
                {"ref": "c", "value": 0}
            ]
        }
    ]
}]

    # Act
    edges = parse_edges(data)

    # Assert
    assert len(edges) == 1
    edge = edges[0]
    assert edge.location == "loc_1"
    assert len(edge.destinations) == 1
    dest = edge.destinations[0]
    assert dest.location == "loc_2"
    assert dest.assignments[0].ref == "c"
    assert dest.assignments[0].value.value == 0
    assert edge.guard is None

def test_parse_desitination_simple():
    from parser import parse_destinations
    
    # Arrange
    data = [{
    "location": "loc_2",
    "assignments": [
        {"ref": "c", "value": 0},
        {"ref": "queue", "value": {"op": "+", "left": "queue", "right": 1}}
    ]
}]

    # Act
    destinations = parse_destinations(data)

    # Assert
    assert len(destinations) == 1
    dest = destinations[0]
    assert dest.location == "loc_2"
    assert dest.assignments[0].ref == "c"
    assert dest.assignments[0].value.value == 0
    assert dest.assignments[1].ref == "queue"
    assert dest.assignments[1].value.op == "+"
    assert dest.assignments[1].value.left.name == "queue"
    assert dest.assignments[1].value.right.value == 1

def test_parse_destinations_with_distribution():
    from parser import parse_destinations
    from models.STA import Distribution
    
    # Arrange
    data = [{
    "location": "loc_2",
    "assignments": [
        {"ref": "c", "value": 0},
        {"ref": "x", "value": {"distribution": "Exponential", "args": [{"op": "/", "left": 1, "right": 6}]}},
    ]
    }]

    # Act
    destinations = parse_destinations(data)

    # Assert
    assert len(destinations) == 1
    dest = destinations[0]
    assert dest.location == "loc_2"
    assert dest.assignments[0].ref == "c"
    assert dest.assignments[0].value.value == 0
    assert dest.assignments[1].ref == "x"
    assert isinstance(dest.assignments[1].value, Distribution)
    assert dest.assignments[1].value.type == "Exponential"
    assert dest.assignments[1].value.args[0].op == "/"
    assert dest.assignments[1].value.args[0].left.value == 1
    assert dest.assignments[1].value.args[0].right.value == 6

def test_parse_assignments_with_literal():
    from parser import parse_assignments
    
    # Arrange
    data = [
        {"ref": "c", "value": 0},
        {"ref": "served_customer", "value": True}
    ]

    # Act
    assignments = parse_assignments(data)

    # Assert
    assert len(assignments) == 2
    assert assignments[0].ref == "c"
    assert assignments[0].value.value == 0
    assert assignments[1].ref == "served_customer"
    assert assignments[1].value.value == True

def test_parse_assignments_with_expression():
    from parser import parse_assignments
    
    # Arrange
    data = [{
    "ref": "queue",
    "value": {"op": "+", "left": "queue", "right": 1}
    }]

    # Act
    assignments = parse_assignments(data)

    # Assert
    assert len(assignments) == 1
    assert assignments[0].ref == "queue"
    assert assignments[0].value.op == "+"
    assert assignments[0].value.left.name == "queue"
    assert assignments[0].value.right.value == 1

def test_parse_assignments_with_distribution():
    from parser import parse_assignments
    from models.STA import Distribution
    
    # Arrange
    data = [
    {"ref": "x", "value": {"distribution": "Exponential", "args": [{"op": "/", "left": 1, "right": 6}]}},
    {"ref": "x", "value": {"distribution": "Normal", "args": [10, 2]}}
    ]

    # Act
    assignments = parse_assignments(data)

    # Assert
    assert len(assignments) == 2
    assert assignments[0].ref == "x"
    assert isinstance(assignments[0].value, Distribution)
    assert assignments[0].value.type == "Exponential"
    assert assignments[0].value.args[0].op == "/"
    assert assignments[0].value.args[0].left.value == 1
    assert assignments[0].value.args[0].right.value == 6
    assert assignments[1].ref == "x"
    assert isinstance(assignments[1].value, Distribution)
    assert assignments[1].value.type == "Normal"
    assert assignments[1].value.args[0].value == 10
    assert assignments[1].value.args[1].value == 2

def test_parse_system_dual():
    from parser import parse_system
    
    # Arrange
    data = {
    "elements": [
        {"automaton": "Arrivals"},
        {"automaton": "Server"}
    ]
    }
    # Act
    system = parse_system(data)

    # Assert
    assert len(system.elements) == 2
    assert system.elements[0].automaton == "Arrivals"
    assert system.elements[1].automaton == "Server"

def test_parse_system_single():
    from parser import parse_system
    
    # Arrange
    data = {
    "elements": [
        {"automaton": "SingleAutomaton"}
    ]
    }
    
    # Act
    system = parse_system(data)

    # Assert
    assert len(system.elements) == 1
    assert system.elements[0].automaton == "SingleAutomaton"