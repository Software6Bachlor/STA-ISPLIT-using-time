import pytest
from models.interval import Interval
from utilities.intervals_intersection import intervals_intersection


# ── 1. No overlap ────────────────────────────────────────────────────────────

def test_disjoint_a_before_b():
    result = intervals_intersection([Interval(1,2,True,True)], [Interval(3,4,True,True)])
    assert result in ([], None)

def test_adjacent_closed_touching_at_point():
    result = intervals_intersection([Interval(1,2,True,True)], [Interval(2,4,True,True)])
    assert len(result) == 1
    assert result[0].lower == 2 and result[0].upper == 2
    assert result[0].include_lower and result[0].include_upper

def test_adjacent_both_open_at_shared_point():
    result = intervals_intersection([Interval(1,2,True,False)], [Interval(2,4,False,True)])
    assert result in ([], None)

def test_adjacent_semi_open_excludes_shared_point():
    result = intervals_intersection([Interval(1,2,True,False)], [Interval(2,4,True,True)])
    assert result in ([], None)


# ── 2. Partial overlap ───────────────────────────────────────────────────────

def test_partial_overlap_closed():
    result = intervals_intersection([Interval(1,3,True,True)], [Interval(2,5,True,True)])
    assert len(result) == 1
    assert result[0].lower == 2 and result[0].upper == 3
    assert result[0].include_lower and result[0].include_upper

def test_partial_overlap_open_lower():
    result = intervals_intersection([Interval(1,3,False,True)], [Interval(2,5,True,True)])
    assert len(result) == 1
    assert result[0].lower == 2 and result[0].upper == 3
    assert result[0].include_lower and result[0].include_upper

def test_partial_overlap_open_upper():
    result = intervals_intersection([Interval(1,3,True,False)], [Interval(2,5,True,True)])
    assert len(result) == 1
    assert result[0].lower == 2 and result[0].upper == 3
    assert result[0].include_lower and not result[0].include_upper

def test_partial_overlap_both_open():
    result = intervals_intersection([Interval(1,3,False,False)], [Interval(2,5,False,True)])
    assert len(result) == 1
    assert result[0].lower == 2 and result[0].upper == 3
    assert not result[0].include_lower and not result[0].include_upper


# ── 3. Containment ───────────────────────────────────────────────────────────

def test_a_contains_b():
    result = intervals_intersection([Interval(1,10,True,True)], [Interval(3,7,True,True)])
    assert len(result) == 1
    assert result[0].lower == 3 and result[0].upper == 7
    assert result[0].include_lower and result[0].include_upper

def test_b_contains_a():
    result = intervals_intersection([Interval(3,7,True,True)], [Interval(1,10,True,True)])
    assert len(result) == 1
    assert result[0].lower == 3 and result[0].upper == 7
    assert result[0].include_lower and result[0].include_upper

def test_a_contains_b_open_bounds():
    result = intervals_intersection([Interval(1,10,True,True)], [Interval(3,7,False,False)])
    assert len(result) == 1
    assert result[0].lower == 3 and result[0].upper == 7
    assert not result[0].include_lower and not result[0].include_upper

def test_identical_closed():
    result = intervals_intersection([Interval(2,5,True,True)], [Interval(2,5,True,True)])
    assert len(result) == 1
    assert result[0].lower == 2 and result[0].upper == 5
    assert result[0].include_lower and result[0].include_upper

def test_identical_open():
    result = intervals_intersection([Interval(2,5,False,False)], [Interval(2,5,False,False)])
    assert len(result) == 1
    assert result[0].lower == 2 and result[0].upper == 5
    assert not result[0].include_lower and not result[0].include_upper

def test_identical_lower_one_open():
    # [2,5] ∩ (2,5] → lower must be open
    result = intervals_intersection([Interval(2,5,True,True)], [Interval(2,5,False,True)])
    assert len(result) == 1
    assert result[0].lower == 2 and result[0].upper == 5
    assert not result[0].include_lower and result[0].include_upper

def test_identical_upper_one_open():
    # [2,5] ∩ [2,5) → upper must be open
    result = intervals_intersection([Interval(2,5,True,True)], [Interval(2,5,True,False)])
    assert len(result) == 1
    assert result[0].lower == 2 and result[0].upper == 5
    assert result[0].include_lower and not result[0].include_upper


# ── 4. Single-point intervals ────────────────────────────────────────────────

def test_point_overlapping_range():
    result = intervals_intersection([Interval(3,3,True,True)], [Interval(1,5,True,True)])
    assert len(result) == 1
    assert result[0].lower == 3 and result[0].upper == 3
    assert result[0].include_lower and result[0].include_upper

def test_two_identical_points():
    result = intervals_intersection([Interval(3,3,True,True)], [Interval(3,3,True,True)])
    assert len(result) == 1
    assert result[0].lower == 3 and result[0].upper == 3
    assert result[0].include_lower and result[0].include_upper

def test_two_different_point_intervals():
    result = intervals_intersection([Interval(2,2,True,True)], [Interval(5,5,True,True)])
    assert result in ([], None)


# ── 5. Multiple intervals / pointer advancement ──────────────────────────────

def test_multiple_overlaps_classic():
    A = [Interval(0,2,True,True), Interval(5,10,True,True), Interval(13,23,True,True)]
    B = [Interval(1,5,True,True), Interval(8,12,True,True), Interval(15,24,True,True), Interval(25,26,True,True)]
    result = intervals_intersection(A, B)
    assert len(result) == 4
    assert result[0].lower == 1  and result[0].upper == 2
    assert result[1].lower == 5  and result[1].upper == 5
    assert result[2].lower == 8  and result[2].upper == 10
    assert result[3].lower == 15 and result[3].upper == 23

def test_a_exhausted_early():
    result = intervals_intersection(
        [Interval(1,2,True,True)],
        [Interval(1,2,True,True), Interval(3,4,True,True), Interval(5,6,True,True)]
    )
    assert len(result) == 1
    assert result[0].lower == 1 and result[0].upper == 2

def test_b_exhausted_early():
    result = intervals_intersection(
        [Interval(1,2,True,True), Interval(3,4,True,True), Interval(5,6,True,True)],
        [Interval(1,2,True,True)]
    )
    assert len(result) == 1
    assert result[0].lower == 1 and result[0].upper == 2

def test_equal_endpoints_both_advance():
    # end_a == end_b == 3, both closed → both i and j must advance
    A = [Interval(1,3,True,True), Interval(3,5,True,True)]
    B = [Interval(2,3,True,True), Interval(3,6,True,True)]
    result = intervals_intersection(A, B)
    assert len(result) == 2
    assert result[0].lower == 2 and result[0].upper == 3
    assert result[1].lower == 3 and result[1].upper == 5

def test_equal_endpoints_a_inclusive_b_exclusive_advances_j_only():
    # end_a == end_b == 3; A includes 3, B excludes 3 → only j advances
    # [1,3] ∩ [2,3) = [2,3);  then i stays, j moves to [4,7]
    # [1,3] ∩ [4,7] = empty
    A = [Interval(1,3,True,True),  Interval(3,6,True,True)]
    B = [Interval(2,3,True,False), Interval(4,7,True,True)]
    result = intervals_intersection(A, B)
    assert len(result) == 2
    assert result[0].lower == 2 and result[0].upper == 3
    assert result[0].include_lower and not result[0].include_upper

def test_equal_endpoints_a_exclusive_b_inclusive_advances_i_only():
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

def test_both_empty():
    assert intervals_intersection([], []) in ([], None)

def test_a_empty():
    assert intervals_intersection([], [Interval(1,5,True,True)]) in ([], None)

def test_b_empty():
    assert intervals_intersection([Interval(1,5,True,True)], []) in ([], None)


# ── 7. Return value contract ─────────────────────────────────────────────────

def test_no_overlap_return_type():
    result = intervals_intersection([Interval(1,2,True,True)], [Interval(3,4,True,True)])
    assert result == [] or result is None

def test_overlap_returns_nonempty_list():
    result = intervals_intersection([Interval(1,5,True,True)], [Interval(2,4,True,True)])
    assert isinstance(result, list) and len(result) > 0