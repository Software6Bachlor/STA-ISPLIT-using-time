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

@pytest.mark.parametrize("clocks,constraints_dmb1,constraints_dmb2,expected_constraints", [
    # 19 <= x <= 20 intersect with 19.5 <= x <= 20  =>  19.5 <= x <= 20
    (["x"],
     [("x", "0", 20), ("0", "x", -19)],      # dmb1: 19 <= x <= 20
     [("x", "0", 20), ("0", "x", -19.5)],    # dmb2: 19.5 <= x <= 20
     [("x", "0", 20), ("0", "x", -19.5)]),   # expected: 19.5 <= x <= 20

    # Simple intersection: clk1 - clk2 <= 5 intersect with clk1 - clk2 <= 3 => clk1 - clk2 <= 3
    (["clk1", "clk2"],
     [("clk1", "clk2", 5)],                  # dmb1
     [("clk1", "clk2", 3)],                  # dmb2
     [("clk1", "clk2", 3)]),                 # expected: tighter constraint

    # Intersecting different constraints: x <= 10, y <= 5 with x <= 8, y <= 7  =>  x <= 8, y <= 5
    (["x", "y"],
     [("x", "0", 10), ("y", "0", 5)],        # dmb1: x <= 10, y <= 5
     [("x", "0", 8), ("y", "0", 7)],         # dmb2: x <= 8, y <= 7
     [("x", "0", 8), ("y", "0", 5)]),        # expected: min of each constraint

    # Multiple clocks with bounds
    (["x", "y"],
     [("x", "0", 15), ("0", "x", -10), ("y", "0", 20)],  # dmb1: 10 <= x <= 15, y <= 20
     [("x", "0", 12), ("0", "x", -11), ("y", "0", 18)],  # dmb2: 11 <= x <= 12, y <= 18
     [("x", "0", 12), ("0", "x", -11), ("y", "0", 18)]), # expected: 11 <= x <= 12, y <= 18
])
def test_DMB_intersection(clocks, constraints_dmb1, constraints_dmb2, expected_constraints):
    # Arrange
    dmb1 = DMB(clocks)
    for c1, c2, bound in constraints_dmb1:
        dmb1.addConstraint(c1, c2, bound)

    dmb2 = DMB(clocks)
    for c1, c2, bound in constraints_dmb2:
        dmb2.addConstraint(c1, c2, bound)

    # Act
    dmb1.intersection(dmb2)

    # Assert
    for c1, c2, expected_bound in expected_constraints:
        i = dmb1.clocks.index(c1)
        j = dmb1.clocks.index(c2)
        assert dmb1.M[i][j] == expected_bound

def test_DMB_union():
    # TODO: implement test for union of two DMBs
    pass

def test_DMB_isEmpty_true():
    # TODO: implement test for checking if a DMB is empty (i.e. has no valid clock valuations)
    pass

def test_DMB_isEmpty_false():
    # TODO: implement test for checking if a DMB is empty check if i,i is < 0 after norm)
    pass

def test_DMB_isSubset_true():
    # TODO: implement test for checking if one DMB is a subset of another (i.e. all constraints of one DMB are satisfied by the other)
    pass

def test_DMB_isSubset_false():
    # TODO: implement test for checking if one DMB is not a subset of another (i.e. there exists at least one constraint in one DMB that is not satisfied by the other)
    pass
