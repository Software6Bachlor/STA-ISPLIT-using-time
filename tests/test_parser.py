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
    
    # Arrange
    data = [
        {"name": "x", "type": "int", "initial_value": 0},
        {"name": "y", "type": "bool"}
    ]

    # Act
    variables = parse_variables(data)

    # Assert
    assert len(variables) == 2
    assert variables[0].name == "x"
    assert variables[0].type == "int"
    assert variables[0].initial_value == 0
    assert variables[1].name == "y"
    assert variables[1].type == "bool"
    assert variables[1].initial_value is None

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