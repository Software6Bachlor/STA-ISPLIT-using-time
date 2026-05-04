from models.Interval import Interval
from utilities.sample_delay import sample_delay_50_50
import random

import pytest
from unittest.mock import patch

# Assuming your code is in a file named `engine.py`
# from engine import Interval, sample_delay, MAX_TIME_BOUND

# ==========================================
# 1. DISCRETE / POINT INTERVAL TESTS
# ==========================================

def test_sampleDelay_pureDiscrete():
    """If only an urgent edge [3, 3] is available, it must return 3.0."""
    intervals = [Interval(3.0, 3.0, True, True)]
    assert sample_delay_50_50(intervals) == 3.0

def test_sampleDelay_invalidDiscreteRaisesError():
    """An open point interval like (3, 3) is an empty set and should raise an error."""
    intervals = [Interval(3.0, 3.0, False, False)]
    with pytest.raises(ValueError, match="empty or invalid"):
        sample_delay_50_50(intervals)

# ==========================================
# 2. CONTINUOUS INTERVAL TESTS
# ==========================================

@patch('random.uniform')
def test_sampleDelay_singleContinuous(mock_uniform):
    """Testing [0, 10]. We mock the RNG to pick exactly the middle (5.0)."""
    intervals = [Interval(0.0, 10.0, True, True)]
    
    mock_uniform.return_value = 5.0
    assert sample_delay_50_50(intervals) == 5.0

@patch('random.uniform')
def test_sampleDelay_disjointContinuous(mock_uniform):
    """
    Testing [0, 2] and [4, 8]. 
    Total valid length = 2 + 4 = 6.
    If RNG rolls 4.0, it should skip the first interval (length 2), 
    leaving an offset of 2.0 to apply to the second interval: 4.0 + 2.0 = 6.0.
    """
    intervals = [Interval(0.0, 2.0, True, True), Interval(4.0, 8.0, True, True)]
    
    mock_uniform.return_value = 4.0
    assert sample_delay_50_50(intervals) == 6.0

# ==========================================
# 3. MIXED SCHEDULER TESTS (The 50/50 Coin Flip)
# ==========================================

@patch('random.random')
@patch('random.choice')
def test_sampleDelay_mixedScheduler_picksDiscrete(mock_choice, mock_random):
    """Force the 50/50 coin flip to be < 0.5 (Heads). It should snap to the boundary."""
    intervals = [Interval(2.0, 10.0, True, True), Interval(3.0, 3.0, True, True)]
    
    mock_random.return_value = 0.1  # Less than 0.5 triggers discrete
    mock_choice.return_value = 3.0  # Force it to pick 3.0 from the discrete list
    
    assert sample_delay_50_50(intervals) == 3.0

@patch('random.random')
@patch('random.uniform')
def test_sampleDelay_mixedScheduler_picksContinuous(mock_uniform, mock_random):
    """Force the 50/50 coin flip to be >= 0.5 (Tails). It should sample continuous."""
    intervals = [Interval(2.0, 10.0, True, True), Interval(3.0, 3.0, True, True)]
    
    mock_random.return_value = 0.8  # Greater than 0.5 triggers continuous
    mock_uniform.return_value = 2.5 # Sample 2.5 from the continuous range
    
    # 2.5 + lower bound 2.0 = 4.5
    assert sample_delay_50_50(intervals) == 4.5

# ==========================================
# 4. EXTREME EDGE CASES (Infinity & Epsilon)
# ==========================================

@patch('random.uniform')
def test_sampleDelay_infinityIsCapped(mock_uniform):
    """
    Testing [5, inf]. 
    Assuming MAX_TIME_BOUND = 10000. The cap should be 5 + 10000 = 10005.
    Total length = 10000. If we roll the absolute max, it should return 10005.
    """
    intervals = [Interval(5.0, float('inf'), True, False)]
    
    mock_uniform.return_value = 10000.0  # Roll the maximum possible length
    assert sample_delay_50_50(intervals) == 10005.0

@patch('random.uniform')
def test_sampleDelay_epsilonNudgeLowerBound(mock_uniform):
    """Testing (0, 5]. If RNG hits exactly 0.0, it must nudge to 1e-9."""
    intervals = [Interval(0.0, 5.0, False, True)] # include_lower is False
    
    mock_uniform.return_value = 0.0 
    assert sample_delay_50_50(intervals) == 1e-9

@patch('random.uniform')
def test_sampleDelay_epsilonNudgeUpperBound(mock_uniform):
    """Testing [0, 5). If RNG hits exactly length 5.0, it must nudge back to 5 - 1e-9."""
    intervals = [Interval(0.0, 5.0, True, False)] # include_upper is False
    
    mock_uniform.return_value = 5.0 
    assert sample_delay_50_50(intervals) == 5.0 - 1e-9