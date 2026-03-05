import pytest

from importanceFunctionBuilder import hopDistanceDictBuilder
from models.STA import Location, Edge, Expression, destination, Automaton


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
            Edge(location=loc_a, guards=[], destinations=[destination(location=loc_b, assignments=[])]),
            Edge(location=loc_b, guards=[], destinations=[destination(location=loc_c, assignments=[])]),
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
                destination(location=loc_b, assignments=[]),
                destination(location=loc_c, assignments=[])
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
                destination(location=loc_b, assignments=[]),
                destination(location=loc_c, assignments=[])
            ]),
            Edge(location=loc_b, guards=[], destinations=[destination(location=loc_d, assignments=[])]),
            Edge(location=loc_c, guards=[], destinations=[destination(location=loc_d, assignments=[])]),
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
            Edge(location=loc_a, guards=[], destinations=[destination(location=loc_b, assignments=[])]),
            Edge(location=loc_b, guards=[], destinations=[destination(location=loc_c, assignments=[])]),
            Edge(location=loc_c, guards=[], destinations=[destination(location=loc_a, assignments=[])]),
        ])

def testHopDistanceDictBuilderSimpleLinearAutomatonFromC(simpleLinearAutomaton):
    """Verify distances in a simple linear Automaton A -> B -> C Starting from C"""
    # Arrange
    automaton: Automaton = simpleLinearAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton["locations"]["loc_c"], automaton["locations"], automaton["edges"])

    # Assert
    assert result[automaton["locations"][0]] == 2 # A
    assert result[automaton["locations"][1]] == 1 # B
    assert result[automaton["locations"][2]] == 0 # C

def testHopDistanceDictBuilderSimpleLinearAutomatonFromB(simpleLinearAutomaton):
    """Verify distances in a simple linear Automaton A -> B -> C Starting from B"""
    # Arrange
    automaton: Automaton = simpleLinearAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton["locations"]["loc_b"], automaton["locations"], automaton["edges"])

    # Assert
    assert result[automaton["locations"][0]] == 1 # A
    assert result[automaton["locations"][1]] == 0 # B
    assert result[automaton["locations"][2]] not in result # C

def testHopDistanceDictBuilderSimpleLinearAutomatonFromA(simpleLinearAutomaton):
    """Verify distances in a simple linear Automaton A -> B -> C Starting from A"""
    # Arrange
    automaton: Automaton = simpleLinearAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton["locations"]["loc_c"], automaton["locations"], automaton["edges"])

    # Assert
    assert result[automaton["locations"][0]] == 0 # A
    assert result[automaton["locations"][1]] not in result # B
    assert result[automaton["locations"][2]] not in result  # C

def testHopDistanceDictBuilderBranchingAutomatonFromC(branchingAutomaton):
    """Verify distances for branches A -> B, A -> C"""
    # Arrange
    automaton: Automaton = branchingAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton["locations"]["loc_c"], automaton["locations"], automaton["edges"])

    # Assert
    assert result[automaton["locations"][0]] == 1 # A
    assert result[automaton["locations"][1]] not in result # B
    assert result[automaton["locations"][2]] == 0 # C

def testHopDistanceDictBuilderBranchingAutomatonFromB(branchingAutomaton):
    """Verify distances for branches A -> B, A -> C"""
    # Arrange
    automaton: Automaton = branchingAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton["locations"]["loc_b"], automaton["locations"], automaton["edges"])

    # Assert
    assert result[automaton["locations"][0]] == 1 # A
    assert result[automaton["locations"][1]] == 0 # B
    assert result[automaton["locations"][2]] not in result # C

def testHopDistanceDictBuilderBranchingAutomatonFromA(branchingAutomaton):
    """Verify distances for branches A -> B, A -> C"""
    # Arrange
    automaton: Automaton = branchingAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton["locations"]["loc_a"], automaton["locations"], automaton["edges"])

    # Assert
    assert result[automaton["locations"][0]] == 0 # A
    assert result[automaton["locations"][1]] not in result # B
    assert result[automaton["locations"][2]] not in result  # C

def testHopDistanceDictBuilderDiamondAutomatonFromA(diamondAutomaton):
    """Verify shortest path in diamond Automaton"""
    # Arrange
    automaton: Automaton = diamondAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton["locations"]["loc_a"], automaton["locations"], automaton["edges"])

    # Assert
    assert result[automaton["locations"][0]] == 0 # A
    assert result[automaton["locations"][1]] not in result # B
    assert result[automaton["locations"][2]] not in result # C
    assert result[automaton["locations"][3]] not in result # D

def testHopDistanceDictBuilderDiamondAutomatonFromB(diamondAutomaton):
    """Verify shortest path in diamond Automaton"""
    # Arrange
    automaton: Automaton = diamondAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton["locations"]["loc_b"], automaton["locations"], automaton["edges"])

    # Assert
    assert result[automaton["locations"][0]] == 1 # A
    assert result[automaton["locations"][1]] == 0 # B
    assert result[automaton["locations"][2]] not in result # C
    assert result[automaton["locations"][3]] not in result # D

def testHopDistanceDictBuilderDiamondAutomatonFromC(diamondAutomaton):
    """Verify shortest path in diamond Automaton"""
    # Arrange
    automaton: Automaton = diamondAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton["locations"]["loc_c"], automaton["locations"], automaton["edges"])

    # Assert
    assert result[automaton["locations"][0]] == 1 # A
    assert result[automaton["locations"][1]] not in result # B
    assert result[automaton["locations"][2]] == 0 # C
    assert result[automaton["locations"][3]] not in result # D

def testHopDistanceDictBuilderDiamondAutomatonFromD(diamondAutomaton):
    """Verify shortest path in diamond Automaton"""
    # Arrange
    automaton: Automaton = diamondAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton["locations"]["loc_d"], automaton["locations"], automaton["edges"])

    # Assert
    assert result[automaton["locations"][0]] == 2 # A
    assert result[automaton["locations"][1]] == 1 # B
    assert result[automaton["locations"][2]] == 1 # C
    assert result[automaton["locations"][3]] == 0 # D

def testHopDistanceDictBuilderCyclicAutomatonFromA(cyclicAutomaton):
    """Verify BFS handles cycles correctly without infinite loops"""
    # Arrange
    automaton: Automaton = cyclicAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton["locations"]["loc_a"], automaton["locations"], automaton["edges"])

    # Assert
    assert result[automaton["locations"][0]] == 0 # A
    assert result[automaton["locations"][1]] == 2 # B
    assert result[automaton["locations"][2]] == 1 # C

def testHopDistanceDictBuilderCyclicAutomatonFromB(cyclicAutomaton):
    """Verify BFS handles cycles correctly without infinite loops"""
    # Arrange
    automaton: Automaton = cyclicAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton["locations"]["loc_b"], automaton["locations"], automaton["edges"])

    # Assert
    assert result[automaton["locations"][0]] == 1 # A
    assert result[automaton["locations"][1]] == 0 # B
    assert result[automaton["locations"][2]] == 2 # C

def testHopDistanceDictBuilderCyclicAutomatonFromC(cyclicAutomaton):
    """Verify BFS handles cycles correctly without infinite loops"""
    # Arrange
    automaton: Automaton = cyclicAutomaton

    # Act
    result = hopDistanceDictBuilder(automaton["locations"]["loc_c"], automaton["locations"], automaton["edges"])

    # Assert
    assert result[automaton["locations"][0]] == 2 # A
    assert result[automaton["locations"][1]] == 1 # B
    assert result[automaton["locations"][2]] == 0 # C

def testHopDistanceDictBuilderSingleNode():
    """Verify single isolated node returns distance 0"""
    # Arrange
    loc_a = Location(name="A", timeProgress=Expression(op="constant", operands={"value": 1}))
    start = loc_a
    locations = [loc_a]
    edges = []

    # Act
    result = hopDistanceDictBuilder(start, locations, edges)

    # Assert
    assert result[loc_a] == 0
    assert len(result) == 1

def testHopDistanceDictBuilderDisconnectedAutomaton():
    """Verify unreachable nodes are not included in result"""
    # Arrange
    loc_a = Location(name="A", timeProgress=Expression(op="constant", operands={"value": 1}))
    loc_b = Location(name="B", timeProgress=Expression(op="constant", operands={"value": 1}))
    loc_c = Location(name="C", timeProgress=Expression(op="constant", operands={"value": 1}))

    start = loc_b
    locations = [loc_a, loc_b, loc_c]
    edges = [
        Edge(location=loc_a, guards=[], destinations=[destination(location=loc_b, assignments=[])]),
    ]

    # Act
    result = hopDistanceDictBuilder(start, locations, edges)

    # Assert
    assert result[loc_a] == 1 # A
    assert result[loc_b] == 0 # B
    assert loc_c not in result
