import pytest
from models.interval import Interval
from utilities.intervals_intersection import intervals_intersection
from utilities.intervals_union import intervals_union


# ── 1. No overlap ────────────────────────────────────────────────────────────

def test_intervalsIntersection_disjointABeforeB():
    result = intervals_intersection([Interval(1,2,True,True)], [Interval(3,4,True,True)])
    assert result in ([], None)

def test_intervalsIntersection_adjacentClosedTouchingAtPoint():
    result = intervals_intersection([Interval(1,2,True,True)], [Interval(2,4,True,True)])
    assert len(result) == 1
    assert result[0].lower == 2 and result[0].upper == 2
    assert result[0].include_lower and result[0].include_upper

def test_intervalsIntersection_adjacentBothOpenAtSharedPoint():
    result = intervals_intersection([Interval(1,2,True,False)], [Interval(2,4,False,True)])
    assert result in ([], None)

def test_intervalsIntersection_adjacentSemiOpenExcludesSharedPoint():
    result = intervals_intersection([Interval(1,2,True,False)], [Interval(2,4,True,True)])
    assert result in ([], None)


# ── 2. Partial overlap ───────────────────────────────────────────────────────

def test_intervalsIntersection_partialOverlapClosed():
    result = intervals_intersection([Interval(1,3,True,True)], [Interval(2,5,True,True)])
    assert len(result) == 1
    assert result[0].lower == 2 and result[0].upper == 3
    assert result[0].include_lower and result[0].include_upper

def test_intervalsIntersection_partialOverlapOpenLower():
    result = intervals_intersection([Interval(1,3,False,True)], [Interval(2,5,True,True)])
    assert len(result) == 1
    assert result[0].lower == 2 and result[0].upper == 3
    assert result[0].include_lower and result[0].include_upper

def test_intervalsIntersection_partialOverlapOpenUpper():
    result = intervals_intersection([Interval(1,3,True,False)], [Interval(2,5,True,True)])
    assert len(result) == 1
    assert result[0].lower == 2 and result[0].upper == 3
    assert result[0].include_lower and not result[0].include_upper

def test_intervalsIntersection_partialOverlapBothOpen():
    result = intervals_intersection([Interval(1,3,False,False)], [Interval(2,5,False,True)])
    assert len(result) == 1
    assert result[0].lower == 2 and result[0].upper == 3
    assert not result[0].include_lower and not result[0].include_upper


# ── 3. Containment ───────────────────────────────────────────────────────────

def test_intervalsIntersection_aContainsB():
    result = intervals_intersection([Interval(1,10,True,True)], [Interval(3,7,True,True)])
    assert len(result) == 1
    assert result[0].lower == 3 and result[0].upper == 7
    assert result[0].include_lower and result[0].include_upper

def test_intervalsIntersection_bContainsA():
    result = intervals_intersection([Interval(3,7,True,True)], [Interval(1,10,True,True)])
    assert len(result) == 1
    assert result[0].lower == 3 and result[0].upper == 7
    assert result[0].include_lower and result[0].include_upper

def test_intervalsIntersection_aContainsBOpenBounds():
    result = intervals_intersection([Interval(1,10,True,True)], [Interval(3,7,False,False)])
    assert len(result) == 1
    assert result[0].lower == 3 and result[0].upper == 7
    assert not result[0].include_lower and not result[0].include_upper

def test_intervalsIntersection_identicalClosed():
    result = intervals_intersection([Interval(2,5,True,True)], [Interval(2,5,True,True)])
    assert len(result) == 1
    assert result[0].lower == 2 and result[0].upper == 5
    assert result[0].include_lower and result[0].include_upper

def test_intervalsIntersection_identicalOpen():
    result = intervals_intersection([Interval(2,5,False,False)], [Interval(2,5,False,False)])
    assert len(result) == 1
    assert result[0].lower == 2 and result[0].upper == 5
    assert not result[0].include_lower and not result[0].include_upper

def test_intervalsIntersection_identicalLowerOneOpen():
    # [2,5] ∩ (2,5] → lower must be open
    result = intervals_intersection([Interval(2,5,True,True)], [Interval(2,5,False,True)])
    assert len(result) == 1
    assert result[0].lower == 2 and result[0].upper == 5
    assert not result[0].include_lower and result[0].include_upper

def test_intervalsIntersection_identicalUpperOneOpen():
    # [2,5] ∩ [2,5) → upper must be open
    result = intervals_intersection([Interval(2,5,True,True)], [Interval(2,5,True,False)])
    assert len(result) == 1
    assert result[0].lower == 2 and result[0].upper == 5
    assert result[0].include_lower and not result[0].include_upper


# ── 4. Single-point intervals ────────────────────────────────────────────────

def test_intervalsIntersection_pointOverlappingRange():
    result = intervals_intersection([Interval(3,3,True,True)], [Interval(1,5,True,True)])
    assert len(result) == 1
    assert result[0].lower == 3 and result[0].upper == 3
    assert result[0].include_lower and result[0].include_upper

def test_intervalsIntersection_twoIdenticalPoints():
    result = intervals_intersection([Interval(3,3,True,True)], [Interval(3,3,True,True)])
    assert len(result) == 1
    assert result[0].lower == 3 and result[0].upper == 3
    assert result[0].include_lower and result[0].include_upper

def test_intervalsIntersection_twoDifferentPointIntervals():
    result = intervals_intersection([Interval(2,2,True,True)], [Interval(5,5,True,True)])
    assert result in ([], None)


# ── 5. Multiple intervals / pointer advancement ──────────────────────────────

def test_intervalsIntersection_multipleOverlapsClassic():
    A = [Interval(0,2,True,True), Interval(5,10,True,True), Interval(13,23,True,True)]
    B = [Interval(1,5,True,True), Interval(8,12,True,True), Interval(15,24,True,True), Interval(25,26,True,True)]
    result = intervals_intersection(A, B)
    assert len(result) == 4
    assert result[0].lower == 1  and result[0].upper == 2
    assert result[1].lower == 5  and result[1].upper == 5
    assert result[2].lower == 8  and result[2].upper == 10
    assert result[3].lower == 15 and result[3].upper == 23

def test_intervalsIntersection_aExhaustedEarly():
    result = intervals_intersection(
        [Interval(1,2,True,True)],
        [Interval(1,2,True,True), Interval(3,4,True,True), Interval(5,6,True,True)]
    )
    assert len(result) == 1
    assert result[0].lower == 1 and result[0].upper == 2

def test_intervalsIntersection_bExhaustedEarly():
    result = intervals_intersection(
        [Interval(1,2,True,True), Interval(3,4,True,True), Interval(5,6,True,True)],
        [Interval(1,2,True,True)]
    )
    assert len(result) == 1
    assert result[0].lower == 1 and result[0].upper == 2

def test_intervalsIntersection_equalEndpointsBothAdvance():
    # end_a == end_b == 3, both closed → both i and j must advance
    A = [Interval(1,3,True,True), Interval(3,5,True,True)]
    B = [Interval(2,3,True,True), Interval(3,6,True,True)]
    result = intervals_intersection(A, B)
    assert len(result) == 2
    assert result[0].lower == 2 and result[0].upper == 3
    assert result[1].lower == 3 and result[1].upper == 5

def test_intervalsIntersection_equalEndpointsAInclusiveBExclusiveAdvancesJOnly():
    # end_a == end_b == 3; A includes 3, B excludes 3 → only j advances
    # [1,3] ∩ [2,3) = [2,3);  then i stays, j moves to [4,7]
    # [1,3] ∩ [4,7] = empty
    A = [Interval(1,3,True,True),  Interval(3,6,True,True)]
    B = [Interval(2,3,True,False), Interval(4,7,True,True)]
    result = intervals_intersection(A, B)
    assert len(result) == 2
    assert result[0].lower == 2 and result[0].upper == 3
    assert result[0].include_lower and not result[0].include_upper

def test_intervalsIntersection_equalEndpointsAExclusiveBInclusiveAdvancesIOnly():
    # end_a == end_b == 3; A excludes 3, B includes 3 → only i advances
    # [1,3) ∩ [2,3] = [2,3);  then j stays, i moves to [4,7]
    # [4,7] ∩ [2,3] = empty
    A = [Interval(1,3,True,False), Interval(4,7,True,True)]
    B = [Interval(2,3,True,True),  Interval(3,6,True,True)]
    result = intervals_intersection(A, B)
    assert len(result) == 2
    assert result[0].lower == 2 and result[0].upper == 3
    assert result[0].include_lower and not result[0].include_upper
    assert result[1].lower == 4 and result[1].upper == 6


# ── 6. Empty inputs ──────────────────────────────────────────────────────────

def test_intervalsIntersection_bothEmpty():
    assert intervals_intersection([], []) in ([], None)

def test_intervalsIntersection_aEmpty():
    assert intervals_intersection([], [Interval(1,5,True,True)]) in ([], None)

def test_intervalsIntersection_bEmpty():
    assert intervals_intersection([Interval(1,5,True,True)], []) in ([], None)


# ── 7. Return value contract ─────────────────────────────────────────────────

def test_intervalsIntersection_noOverlapReturnType():
    result = intervals_intersection([Interval(1,2,True,True)], [Interval(3,4,True,True)])
    assert result == [] or result is None

def test_intervalsIntersection_overlapReturnsNonemptyList():
    result = intervals_intersection([Interval(1,5,True,True)], [Interval(2,4,True,True)])
    assert isinstance(result, list) and len(result) > 0


# Tests for union. ─────────────────────────────────────────────────

# --- Helper Function for Testing ---
def assert_intervals_equal(result: list[Interval], expected: list[Interval]):
    """Helper to compare interval properties"""
    assert len(result) == len(expected), f"Expected {len(expected)} intervals, got {len(result)}"
    for r, e in zip(result, expected):
        assert r.lower == e.lower, f"Lower bounds differ: {r.lower} != {e.lower}"
        assert r.upper == e.upper, f"Upper bounds differ: {r.upper} != {e.upper}"
        assert r.include_lower == e.include_lower, f"Lower inclusion differs for {r.lower}"
        assert r.include_upper == e.include_upper, f"Upper inclusion differs for {r.upper}"

# --- Test Cases ---

def test_intervalsUnion_emptyInput():
    """Test providing no intervals or empty lists."""
    assert intervals_union() == []
    assert intervals_union([]) == []
    assert intervals_union([], []) == []

def test_intervalsUnion_singleInterval():
    """Test providing a single interval."""
    i1 = Interval(1, 5, True, True)
    result = intervals_union([i1])
    assert_intervals_equal(result, [Interval(1, 5, True, True)])

def test_intervalsUnion_disjointIntervals():
    """Test intervals that do not overlap at all."""
    i1 = Interval(1, 5, True, True)   # [1, 5]
    i2 = Interval(10, 15, True, True) # [10, 15]
    result = intervals_union([i1, i2])
    
    expected = [Interval(1, 5, True, True), Interval(10, 15, True, True)]
    assert_intervals_equal(result, expected)

def test_intervalsUnion_standardOverlap():
    """Test overlapping intervals that should merge."""
    i1 = Interval(1, 5, True, True)   # [1, 5]
    i2 = Interval(3, 8, True, True)   # [3, 8]
    result = intervals_union([i1, i2])
    
    expected = [Interval(1, 8, True, True)]
    assert_intervals_equal(result, expected)

def test_intervalsUnion_fullyContainedInterval():
    """Test an interval that is completely inside another."""
    i1 = Interval(1, 10, True, True)  # [1, 10]
    i2 = Interval(3, 5, True, True)   # [3, 5]
    result = intervals_union([i1, i2])
    
    expected = [Interval(1, 10, True, True)]
    assert_intervals_equal(result, expected)

def test_intervalsUnion_containedIntervalExpandsInclusion():
    """Test a contained interval that upgrades the strictness of the bounds."""
    i1 = Interval(1, 10, False, False) # (1, 10)
    i2 = Interval(1, 5, True, True)    # [1, 5]
    result = intervals_union([i1, i2])
    
    # Should become [1, 10)
    expected = [Interval(1, 10, True, False)]
    assert_intervals_equal(result, expected)

def test_intervalsUnion_touchingIntervalsInclusive():
    """Test adjacent intervals where bounds touch and at least one is inclusive."""
    i1 = Interval(1, 5, True, True)   # [1, 5]
    i2 = Interval(5, 10, True, True)  # [5, 10]
    result = intervals_union([i1, i2])
    
    expected = [Interval(1, 10, True, True)]
    assert_intervals_equal(result, expected)

def test_intervalsUnion_touchingIntervalsMixedInclusion():
    """Test adjacent intervals where one includes the bound and the other doesn't."""
    i1 = Interval(1, 5, True, True)   # [1, 5]
    i2 = Interval(5, 10, False, True) # (5, 10]
    result = intervals_union([i1, i2])
    
    expected = [Interval(1, 10, True, True)]
    assert_intervals_equal(result, expected)

def test_intervalsUnion_touchingIntervalsExclusive():
    """
    CRITICAL EDGE CASE:
    Test adjacent intervals where BOTH bounds exclude the touching point.
    They should NOT merge. e.g., [1, 5) U (5, 10] != [1, 10]
    """
    i1 = Interval(1, 5, True, False)  # [1, 5)
    i2 = Interval(5, 10, False, True) # (5, 10]
    result = intervals_union([i1, i2])
    
    expected = [
        Interval(1, 5, True, False), 
        Interval(5, 10, False, True)
    ]
    assert_intervals_equal(result, expected)

def test_intervalsUnion_unsortedInput():
    """Test that the function correctly sorts the intervals before merging."""
    i1 = Interval(10, 15, True, True)
    i2 = Interval(1, 5, True, True)
    i3 = Interval(4, 12, True, True)
    
    # Passing them out of order
    result = intervals_union([i1, i2, i3])
    
    expected = [Interval(1, 15, True, True)]
    assert_intervals_equal(result, expected)

def test_intervalsUnion_multipleListsArgs():
    """Test passing multiple lists as *args."""
    list1 = [Interval(1, 3, True, True), Interval(10, 12, True, True)]
    list2 = [Interval(2, 5, True, True)]
    list3 = [Interval(11, 15, True, True)]
    
    result = intervals_union(list1, list2, list3)
    
    expected = [
        Interval(1, 5, True, True),
        Interval(10, 15, True, True)
    ]
    assert_intervals_equal(result, expected)

def test_intervalsUnion_exactDuplicates():
    """Test multiple exact same intervals."""
    i1 = Interval(2, 4, True, False)
    i2 = Interval(2, 4, True, False)
    i3 = Interval(2, 4, True, False)
    
    result = intervals_union([i1, i2, i3])
    
    expected = [Interval(2, 4, True, False)]
    assert_intervals_equal(result, expected)



def test_intervalsNegated_returnsNegatedWhenNo0():
    from utilities.intervals_negated import intervals_negated
    from models.interval import Interval

    assert intervals_negated([Interval(1, 2, False, True)]) == [Interval(0, 1, True, True), Interval(2, float("inf"), False, True)]

def test_intervalsNegated_returnsNegatedWhen0():
    from utilities.intervals_negated import intervals_negated
    from models.interval import Interval
    assert intervals_negated([Interval(0, 2, True, True)]) == [Interval(2, float("inf"), False, True)]


def test_intervalsNegated_returnsNegatedWhenInfand0():
    from utilities.intervals_negated import intervals_negated
    from models.interval import Interval
    assert intervals_negated([Interval(0, float("inf"), True, True)]) == None

def test_intervalsNegated_returnsNegatedWhenInf():
    from utilities.intervals_negated import intervals_negated
    from models.interval import Interval
    
    assert intervals_negated([Interval(1, float("inf"), False, True)]) == [Interval(0, 1, True, True)]

def test_init_raisesValueErrorIfLowerLargerthanUpper():
    from models.interval import Interval
    
    with pytest.raises(ValueError):
        Interval(5, 3, True, True)


def test_eq_returnsFalseIfOtherNotInterval():
    from models.interval import Interval
    i1 = Interval(1, 5, True, True)
    assert (i1 == "not an interval") is False