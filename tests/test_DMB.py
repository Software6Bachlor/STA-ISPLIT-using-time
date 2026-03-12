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
    dmbNew = dmb1.intersection(dmb2)

    # Assert
    for c1, c2, expected_bound in expected_constraints:
        i = dmbNew.clocks.index(c1)
        j = dmbNew.clocks.index(c2)
        assert dmbNew.M[i][j] == expected_bound

@pytest.mark.parametrize("clocks,constraints", [
    # Contradictory bounds on single clock: x >= 10 and x <= 5 (impossible)
    (["x"], [("x", "0", 5), ("0", "x", -10)]),

    # Contradictory difference: x - y <= -5 and y - x <= -10, sum is -15 < 0
    (["x", "y"], [("x", "y", -5), ("y", "x", -10)]),

    # Contradictory cycle: x - y <= 3, y - z <= 2, z - x <= -10 (sum: -5 < 0)
    (["x", "y", "z"], [("x", "y", 3), ("y", "z", 2), ("z", "x", -10)]),

    # Simple contradiction: x >= 20 and x <= 19
    (["x"], [("0", "x", -20), ("x", "0", 19)]),

    # Two clocks with tight contradiction: 11 <= x <= 12 and 15 <= x <= 16
    (["x"], [("0", "x", -11), ("x", "0", 12), ("0", "x", -15), ("x", "0", 16)]),
])
def test_DMB_isEmptyTrue(clocks, constraints):
    # Arrange
    dmb = DMB(clocks)
    for c1, c2, bound in constraints:
        dmb.addConstraint(c1, c2, bound)

    # Act
    dmb.normalize()

    # Assert
    assert dmb.isEmpty() == True


@pytest.mark.parametrize("clocks,constraints", [
    # Freshly initialized DMB with no constraints
    (["x"], []),

    # Consistent bounds: 0 <= x <= 10
    (["x"], [("x", "0", 10), ("0", "x", 0)]),

    # Consistent bounds: 5 <= x <= 15
    (["x"], [("0", "x", -5), ("x", "0", 15)]),

    # Multiple clocks with consistent constraints
    (["x", "y"], [("x", "0", 10), ("0", "x", -5), ("y", "0", 20), ("0", "y", -10)]),

    # Consistent difference constraints: x - y <= 5, y - x <= 3
    (["x", "y"], [("x", "y", 5), ("y", "x", 3)]),

    # Consistent cycle: x - y <= 5, y - z <= 3, z - x <= 2 (sum: 10 >= 0)
    (["x", "y", "z"], [("x", "y", 5), ("y", "z", 3), ("z", "x", 2)]),
])
def test_DMB_isEmptyFalse(clocks, constraints):
    # Arrange
    dmb = DMB(clocks)
    for c1, c2, bound in constraints:
        dmb.addConstraint(c1, c2, bound)

    # Act
    dmb.normalize()

    # Assert
    assert dmb.isEmpty() == False

@pytest.mark.parametrize("clocks,constraints_subset,constraints_superset", [
    # Identical constraints: DMB is a subset of itself
    (["x"], [("x", "0", 10), ("0", "x", -5)], [("x", "0", 10), ("0", "x", -5)]),

    # Tighter upper bound: 5 <= x <= 10 is subset of 5 <= x <= 15
    (["x"], [("x", "0", 10), ("0", "x", -5)], [("x", "0", 15), ("0", "x", -5)]),

    # Tighter lower bound: 10 <= x <= 20 is subset of 5 <= x <= 20
    (["x"], [("x", "0", 20), ("0", "x", -10)], [("x", "0", 20), ("0", "x", -5)]),

    # Tighter bounds on both sides: 10 <= x <= 15 is subset of 5 <= x <= 20
    (["x"], [("x", "0", 15), ("0", "x", -10)], [("x", "0", 20), ("0", "x", -5)]),

    # Multiple clocks: tighter constraints on both
    (["x", "y"],
     [("x", "0", 10), ("0", "x", -5), ("y", "0", 8)],
     [("x", "0", 15), ("0", "x", -3), ("y", "0", 12)]),

    # Tighter difference constraint: x - y <= 3 is subset of x - y <= 5
    (["x", "y"], [("x", "y", 3)], [("x", "y", 5)]),

    # Multiple tighter constraints
    (["x", "y"],
     [("x", "0", 10), ("y", "0", 8), ("x", "y", 3)],
     [("x", "0", 12), ("y", "0", 10), ("x", "y", 5)]),
])
def test_DMB_isSubsetFrue(clocks, constraints_subset, constraints_superset):
    # Arrange
    dmb_subset = DMB(clocks)
    for c1, c2, bound in constraints_subset:
        dmb_subset.addConstraint(c1, c2, bound)

    dmb_superset = DMB(clocks)
    for c1, c2, bound in constraints_superset:
        dmb_superset.addConstraint(c1, c2, bound)

    # Act & Assert
    assert dmb_subset.isSubset(dmb_superset) == True

@pytest.mark.parametrize("clocks,constraints_dmb1,constraints_dmb2", [
    # Looser upper bound: 5 <= x <= 15 is NOT a subset of 5 <= x <= 10
    (["x"], [("x", "0", 15), ("0", "x", -5)], [("x", "0", 10), ("0", "x", -5)]),

    # Looser lower bound: 5 <= x <= 20 is NOT a subset of 10 <= x <= 20
    (["x"], [("x", "0", 20), ("0", "x", -5)], [("x", "0", 20), ("0", "x", -10)]),

    # Looser on both sides: 3 <= x <= 25 is NOT a subset of 10 <= x <= 15
    (["x"], [("x", "0", 25), ("0", "x", -3)], [("x", "0", 15), ("0", "x", -10)]),

    # One tighter, one looser: 5 <= x <= 20 vs 10 <= x <= 15 (neither is subset)
    (["x"], [("x", "0", 20), ("0", "x", -5)], [("x", "0", 15), ("0", "x", -10)]),

    # Multiple clocks: looser on one constraint
    (["x", "y"],
     [("x", "0", 20), ("0", "x", -5), ("y", "0", 10)],
     [("x", "0", 15), ("0", "x", -5), ("y", "0", 10)]),

    # Looser difference constraint: x - y <= 10 is NOT a subset of x - y <= 5
    (["x", "y"], [("x", "y", 10)], [("x", "y", 5)]),

    # Partially overlapping: some constraints tighter, some looser
    (["x", "y"],
     [("x", "0", 8), ("y", "0", 15)],
     [("x", "0", 10), ("y", "0", 12)]),
])
def test_DMB_isSubsetFalse(clocks, constraints_dmb1, constraints_dmb2):
    # Arrange
    dmb1 = DMB(clocks)
    for c1, c2, bound in constraints_dmb1:
        dmb1.addConstraint(c1, c2, bound)

    dmb2 = DMB(clocks)
    for c1, c2, bound in constraints_dmb2:
        dmb2.addConstraint(c1, c2, bound)

    # Act & Assert
    assert dmb1.isSubset(dmb2) == False
