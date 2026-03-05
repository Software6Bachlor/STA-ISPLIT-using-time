import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from importanceFunctionBuilder import hopDistanceDictBuilder


@pytest.fixture
def simple_linear_graph():
    """A -> B -> C"""
    return {
        'start': 'A',
        'states': ['A', 'B', 'C'],
        'edges': {
            'A': ['B'],
            'B': ['C'],
            'C': []
        }
    }


@pytest.fixture
def branching_graph():
    """A -> B, A -> C"""
    return {
        'start': 'A',
        'states': ['A', 'B', 'C'],
        'edges': {
            'A': ['B', 'C'],
            'B': [],
            'C': []
        }
    }


@pytest.fixture
def diamond_graph():
    """A -> B, A -> C, B -> D, C -> D"""
    return {
        'start': 'A',
        'states': ['A', 'B', 'C', 'D'],
        'edges': {
            'A': ['B', 'C'],
            'B': ['D'],
            'C': ['D'],
            'D': []
        }
    }


@pytest.fixture
def cyclic_graph():
    """A -> B -> C -> A"""
    return {
        'start': 'A',
        'states': ['A', 'B', 'C'],
        'edges': {
            'A': ['B'],
            'B': ['C'],
            'C': ['A']
        }
    }


def testHopDistanceDictBuilderSimpleLinearGraph(simple_linear_graph):
    """Verify distances in a simple linear graph A -> B -> C"""
    # Arrange
    graph = simple_linear_graph

    # Act
    result = hopDistanceDictBuilder(graph['start'], graph['states'], graph['edges'])

    # Assert
    assert result['A'] == 0
    assert result['B'] == 1
    assert result['C'] == 2


def testHopDistanceDictBuilderBranchingGraph(branching_graph):
    """Verify equal distances for branches A -> B, A -> C"""
    # Arrange
    graph = branching_graph

    # Act
    result = hopDistanceDictBuilder(graph['start'], graph['states'], graph['edges'])

    # Assert
    assert result['A'] == 0
    assert result['B'] == 1
    assert result['C'] == 1


def testHopDistanceDictBuilderDiamondGraph(diamond_graph):
    """Verify shortest path in diamond graph where multiple paths exist to D"""
    # Arrange
    graph = diamond_graph

    # Act
    result = hopDistanceDictBuilder(graph['start'], graph['states'], graph['edges'])

    # Assert
    assert result['A'] == 0
    assert result['B'] == 1
    assert result['C'] == 1
    assert result['D'] == 2


def testHopDistanceDictBuilderCyclicGraph(cyclic_graph):
    """Verify BFS handles cycles correctly without infinite loops"""
    # Arrange
    graph = cyclic_graph

    # Act
    result = hopDistanceDictBuilder(graph['start'], graph['states'], graph['edges'])

    # Assert
    assert result['A'] == 0
    assert result['B'] == 1
    assert result['C'] == 2


def testHopDistanceDictBuilderSingleNode():
    """Verify single isolated node returns distance 0"""
    # Arrange
    start = 'A'
    states = ['A']
    edges = {'A': []}

    # Act
    result = hopDistanceDictBuilder(start, states, edges)

    # Assert
    assert result['A'] == 0
    assert len(result) == 1


def testHopDistanceDictBuilderDisconnectedGraph():
    """Verify unreachable nodes are not included in result"""
    # Arrange
    start = 'A'
    states = ['A', 'B', 'C']
    edges = {
        'A': ['B'],
        'B': [],
        'C': []  # C is disconnected
    }

    # Act
    result = hopDistanceDictBuilder(start, states, edges)

    # Assert
    assert result['A'] == 0
    assert result['B'] == 1
    assert 'C' not in result
