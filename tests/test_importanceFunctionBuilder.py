import pytest

from importanceFunctionBuilder import hopDistanceDictBuilder
from models.STA import Location, Edge, Expression, Destination, Automaton


@pytest.fixture
def simpleLinearAutomaton():
    """A -> B -> C"""
    loc_a = Location(name="A", timeProgress=Expression(op="constant", operands={"value": 1}))
    loc_b = Location(name="B", timeProgress=Expression(op="constant", operands={"value": 1}))
    loc_c = Location(name="C", timeProgress=Expression(op="constant", operands={"value": 1}))
    return Automaton(
        name="simpleLinear",
        locations=[loc_a, loc_b, loc_c],
        initial_locations=[loc_a],
        variables=[],
        edges=[
            Edge(location=loc_a, guards=[], destinations=[Destination(location=loc_b, assignments=[])]),
            Edge(location=loc_b, guards=[], destinations=[Destination(location=loc_c, assignments=[])]),
        ])

@pytest.fixture
def branchingAutomaton():
    """A -> B, A -> C"""
    loc_a = Location(name="A", timeProgress=Expression(op="constant", operands={"value": 1}))
    loc_b = Location(name="B", timeProgress=Expression(op="constant", operands={"value": 1}))
    loc_c = Location(name="C", timeProgress=Expression(op="constant", operands={"value": 1}))

    return Automaton(
        name="branching",
        locations=[loc_a, loc_b, loc_c],
        initial_locations=[loc_a],
        variables=[],
        edges=[
            Edge(location=loc_a, guards=[], destinations=[
                Destination(location=loc_b, assignments=[]),
                Destination(location=loc_c, assignments=[])
            ]),
        ])

@pytest.fixture
def diamondAutomaton():
    """A -> B, A -> C, B -> D, C -> D"""
    loc_a = Location(name="A", timeProgress=Expression(op="constant", operands={"value": 1}))
    loc_b = Location(name="B", timeProgress=Expression(op="constant", operands={"value": 1}))
    loc_c = Location(name="C", timeProgress=Expression(op="constant", operands={"value": 1}))
    loc_d = Location(name="D", timeProgress=Expression(op="constant", operands={"value": 1}))

    return Automaton(
        name="diamond",
        locations=[loc_a, loc_b, loc_c, loc_d],
        initial_locations=[loc_a],
        variables=[],
        edges=[
            Edge(location=loc_a, guards=[], destinations=[
                Destination(location=loc_b, assignments=[]),
                Destination(location=loc_c, assignments=[])
            ]),
            Edge(location=loc_b, guards=[], destinations=[Destination(location=loc_d, assignments=[])]),
            Edge(location=loc_c, guards=[], destinations=[Destination(location=loc_d, assignments=[])]),
        ])

@pytest.fixture
def cyclicAutomaton():
    """A -> B -> C -> A"""
    loc_a = Location(name="A", timeProgress=Expression(op="constant", operands={"value": 1}))
    loc_b = Location(name="B", timeProgress=Expression(op="constant", operands={"value": 1}))
    loc_c = Location(name="C", timeProgress=Expression(op="constant", operands={"value": 1}))

    return Automaton(
        name="cyclic",
        locations=[loc_a, loc_b, loc_c],
        initial_locations=[loc_a],
        variables=[],
        edges=[
            Edge(location=loc_a, guards=[], destinations=[Destination(location=loc_b, assignments=[])]),
            Edge(location=loc_b, guards=[], destinations=[Destination(location=loc_c, assignments=[])]),
            Edge(location=loc_c, guards=[], destinations=[Destination(location=loc_a, assignments=[])]),
        ])

def test_HopDistanceDictBuilder_SimpleLinearAutomatonFromC(simpleLinearAutomaton):
    """Verify distances in a simple linear Automaton A -> B -> C Starting from C"""
    # Arrange
    automaton: Automaton = simpleLinearAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton.locations[2], automaton.edges)

    # Assert
    assert result["A"] == 2
    assert result["B"] == 1
    assert result["C"] == 0

def test_HopDistanceDictBuilder_SimpleLinearAutomatonFromB(simpleLinearAutomaton):
    """Verify distances in a simple linear Automaton A -> B -> C Starting from B"""
    # Arrange
    automaton: Automaton = simpleLinearAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton.locations[1], automaton.edges)

    # Assert
    assert result["A"] == 1
    assert result["B"] == 0
    assert "C" not in result

def test_HopDistanceDictBuilder_SimpleLinearAutomatonFromA(simpleLinearAutomaton):
    """Verify distances in a simple linear Automaton A -> B -> C Starting from A"""
    # Arrange
    automaton: Automaton = simpleLinearAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton.locations[0], automaton.edges)

    # Assert
    assert result["A"] == 0
    assert "B" not in result
    assert "C" not in result

def test_HopDistanceDictBuilder_BranchingAutomatonFromC(branchingAutomaton):
    """Verify distances for branches A -> B, A -> C"""
    # Arrange
    automaton: Automaton = branchingAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton.locations[2], automaton.edges)

    # Assert
    assert result["A"] == 1
    assert "B" not in result
    assert result["C"] == 0

def test_HopDistanceDictBuilder_BranchingAutomatonFromB(branchingAutomaton):
    """Verify distances for branches A -> B, A -> C"""
    # Arrange
    automaton: Automaton = branchingAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton.locations[1], automaton.edges)

    # Assert
    assert result["A"] == 1
    assert result["B"] == 0
    assert "C" not in result

def test_HopDistanceDictBuilder_BranchingAutomatonFromA(branchingAutomaton):
    """Verify distances for branches A -> B, A -> C"""
    # Arrange
    automaton: Automaton = branchingAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton.locations[0], automaton.edges)

    # Assert
    assert result["A"] == 0
    assert "B" not in result
    assert "C" not in result

def test_HopDistanceDictBuilder_DiamondAutomatonFromA(diamondAutomaton):
    """Verify shortest path in diamond Automaton"""
    # Arrange
    automaton: Automaton = diamondAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton.locations[0], automaton.edges)

    # Assert
    assert result["A"] == 0
    assert "B" not in result
    assert "C" not in result
    assert "D" not in result

def test_HopDistanceDictBuilder_DiamondAutomatonFromB(diamondAutomaton):
    """Verify shortest path in diamond Automaton"""
    # Arrange
    automaton: Automaton = diamondAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton.locations[1], automaton.edges)

    # Assert
    assert result["A"] == 1
    assert result["B"] == 0
    assert "C" not in result
    assert "D" not in result

def test_HopDistanceDictBuilder_DiamondAutomatonFromC(diamondAutomaton):
    """Verify shortest path in diamond Automaton"""
    # Arrange
    automaton: Automaton = diamondAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton.locations[2], automaton.edges)

    # Assert
    assert result["A"] == 1
    assert "B" not in result
    assert result["C"] == 0
    assert "D" not in result

def test_HopDistanceDictBuilder_DiamondAutomatonFromD(diamondAutomaton):
    """Verify shortest path in diamond Automaton"""
    # Arrange
    automaton: Automaton = diamondAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton.locations[3], automaton.edges)

    # Assert
    assert result["A"] == 2
    assert result["B"] == 1
    assert result["C"] == 1
    assert result["D"] == 0

def test_HopDistanceDictBuilder_CyclicAutomatonFromA(cyclicAutomaton):
    """Verify BFS handles cycles correctly without infinite loops"""
    # Arrange
    automaton: Automaton = cyclicAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton.locations[0], automaton.edges)

    # Assert
    assert result["A"] == 0
    assert result["B"] == 2
    assert result["C"] == 1

def test_HopDistanceDictBuilder_CyclicAutomatonFromB(cyclicAutomaton):
    """Verify BFS handles cycles correctly without infinite loops"""
    # Arrange
    automaton: Automaton = cyclicAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton.locations[1], automaton.edges)

    # Assert
    assert result["A"] == 1
    assert result["B"] == 0
    assert result["C"] == 2

def test_HopDistanceDictBuilder_CyclicAutomatonFromC(cyclicAutomaton):
    """Verify BFS handles cycles correctly without infinite loops"""
    # Arrange
    automaton: Automaton = cyclicAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton.locations[2], automaton.edges)

    # Assert
    assert result["A"] == 2
    assert result["B"] == 1
    assert result["C"] == 0

def test_HopDistanceDictBuilder_SingleNode():
    """Verify single isolated node returns distance 0"""
    # Arrange
    loc_a = Location(name="A", timeProgress=Expression(op="constant", operands={"value": 1}))
    start = loc_a
    edges = []

    # Act
    result = hopDistanceDictBuilder(start, edges)

    # Assert
    assert result["A"] == 0
    assert len(result) == 1

def test_HopDistanceDictBuilder_DisconnectedAutomaton():
    """Verify unreachable nodes are not included in result"""
    # Arrange
    loc_a = Location(name="A", timeProgress=Expression(op="constant", operands={"value": 1}))
    loc_b = Location(name="B", timeProgress=Expression(op="constant", operands={"value": 1}))
    loc_c = Location(name="C", timeProgress=Expression(op="constant", operands={"value": 1}))

    start = loc_b
    edges = [
        Edge(location=loc_a, guards=[], destinations=[Destination(location=loc_b, assignments=[])]),
    ]

    # Act
    result = hopDistanceDictBuilder(start, edges)

    # Assert
    assert result["A"] == 1
    assert result["B"] == 0
    assert "C" not in result
