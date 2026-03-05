def test_parse_model():
    from parser import parse_model
    
    # Arrange
    data = {
        "name": "test_model",
        "jani_version": "1.0",
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
        {"name": "x", "type": "int", "initial_value": 0},
        {"name": "y", "type": "bool"},
        {"name": "z", "type": {"kind": "int", "base": 10, "lower_bound": 0, "upper_bound": 100}}
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
    assert properties[0].expression.fun == "fun1"


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
        {"name": "loc1", "timeProgress": {"exp": {"op": "op1", "left": {"value": 1}, "right": {"value": 2}}}},
        {"name": "loc2", "timeProgress": {"exp": {"op": "op2", "left": {"value": 3}, "right": {"value": 4}}}}
    ]

    # Act
    locations = parse_locations(data)

    # Assert
    assert len(locations) == 2
    assert locations[0].name == "loc1"
    assert locations[0].timeProgress.op == "op1"
    assert locations[1].name == "loc2"
    assert locations[1].timeProgress.op == "op2"