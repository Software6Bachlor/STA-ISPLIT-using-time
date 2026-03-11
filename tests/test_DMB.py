import pytest
from DMB import DMB
import math

INF = math.inf

def test_DMB_init():
    # Arrange
    clocks = ["clk1", "clk2", "clk3"]

    # Act
    dmb = DMB(clocks)

    # Assert
    assert dmb.clocks == ["0", "clk1", "clk2", "clk3"]
    assert dmb.n == 4

@pytest.mark.parametrize("input,expected", [
    (5, 5),
    (0, 0),
    (-3, -3),
])
def test_DMB_addConstraint(input, expected):
    # Arrange
    clocks = ["clk1", "clk2"]
    dmb = DMB(clocks)

    # Act
    dmb.addConstraint("clk1", "clk2", input)

    # Assert
    i = dmb.clocks.index("clk1")
    j = dmb.clocks.index("clk2")
    assert dmb.M[i][j] == expected


@pytest.mark.parametrize("clocks,constraints,remove_clock", [
    (["clk1", "clk2", "clk3"], [("clk1", "clk2", 5), ("clk2", "clk3", 3)], "clk2"),
    (["clk1", "clk2", "clk3"], [("clk1", "clk2", 5), ("clk2", "clk3", 3)], "clk1"),
    (["clk1", "clk2", "clk3"], [("clk1", "clk2", 5), ("clk2", "clk3", 3)], "clk3"),
    (["x", "y"], [("x", "0", 10), ("0", "y", -5)], "x"),
    (["x", "y"], [("x", "0", 10), ("0", "y", -5)], "y"),
])
def test_DMB_removeConstrains(clocks, constraints, remove_clock):
    # Arrange
    dmb = DMB(clocks)
    for c1, c2, bound in constraints:
        dmb.addConstraint(c1, c2, bound)

    # Act
    dmb.removeConstrains(remove_clock)

    # Assert
    idx = dmb.clocks.index(remove_clock)
    for i in range(dmb.n):
        if i == idx:
            continue
        assert dmb.M[i][idx] == INF
        assert dmb.M[idx][i] == INF
    assert dmb.M[idx][idx] == 0

@pytest.mark.parametrize("clocks,constraints,expected_constraint", [
    # Simple transitive closure: clk1 - clk2 <= 5, clk2 - clk3 <= 3 => clk1 - clk3 <= 8
    (["clk1", "clk2", "clk3"],
     [("clk1", "clk2", 5), ("clk2", "clk3", 3)],
     ("clk1", "clk3", 8)),

    # Transitive closure with negative bounds
    (["clk1", "clk2", "clk3"],
     [("clk1", "clk2", -2), ("clk2", "clk3", -1)],
     ("clk1", "clk3", -3)),

    # Multiple clocks in chain: clk1 - clk2 <= 2, clk2 - clk3 <= 3, clk3 - clk4 <= 4 => clk1 - clk4 <= 9
    (["clk1", "clk2", "clk3", "clk4"],
     [("clk1", "clk2", 2), ("clk2", "clk3", 3), ("clk3", "clk4", 4)],
     ("clk1", "clk4", 9)),

    # Multiple paths - should choose minimum: direct path 10 vs indirect path 3+5=8
    (["clk1", "clk2", "clk3"],
     [("clk1", "clk2", 10), ("clk1", "clk3", 3), ("clk3", "clk2", 5)],
     ("clk1", "clk2", 8)),

    # Constraints with zero clock: x - 0 <= 10, 0 - y <= -5 => x - y <= 5
    (["x", "y"],
     [("x", "0", 10), ("0", "y", -5)],
     ("x", "y", 5)),

    # Bi-directional constraints: creates tighter bounds
    (["clk1", "clk2", "clk3"],
     [("clk1", "clk2", 5), ("clk2", "clk1", -3), ("clk2", "clk3", 2)],
     ("clk1", "clk3", 7)),
])
def test_DMB_normalize(clocks, constraints, expected_constraint):
    # Arrange
    dmb = DMB(clocks)
    for c1, c2, bound in constraints:
        dmb.addConstraint(c1, c2, bound)

    # Act
    dmb.normalize()

    # Assert
    clock1, clock2, expected_bound = expected_constraint
    i = dmb.clocks.index(clock1)
    j = dmb.clocks.index(clock2)
    assert dmb.M[i][j] == expected_bound
