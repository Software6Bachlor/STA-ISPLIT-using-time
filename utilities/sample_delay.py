import random
import sys
from constants import MAX_TIME_BOUND
from models.interval import Interval

def sample_delay_50_50(delay_intervals: list[Interval]) -> float:
    """
    Samples a continuous delay, safely handling float('inf') and strict open/closed intervals.
    """
    discrete_points = []
    continuous_ranges = []

    # 1 sanitize infinity & categorise intervals
    for interval in delay_intervals:
        safe_upper = interval.upper
        
        if safe_upper == float("inf"):
            safe_upper = max(interval.lower + MAX_TIME_BOUND, MAX_TIME_BOUND)
            is_upper_inclusive = True 
        else:
            is_upper_inclusive = interval.include_upper

        # 2. check for point intervals vs continuous
        if interval.lower == safe_upper:
            if interval.include_lower and is_upper_inclusive:
                discrete_points.append(interval.lower)
            else:
                # eg., (3, 3] or [5, 5). this is an empty set
                continue
        else:
            # Store the full tuple including the includes
            continuous_ranges.append((interval.lower, safe_upper, interval.include_lower, is_upper_inclusive))

    has_discrete = len(discrete_points) > 0
    has_continuous = len(continuous_ranges) > 0

    # 3. The LSS Mixed Scheduler Logic
    if has_discrete and has_continuous:
        if random.random() < 0.5:
            return random.choice(discrete_points)
        else:
            return _sample_continuous(continuous_ranges)
            
    elif has_discrete:
        return random.choice(discrete_points)
        
    elif has_continuous:
        return _sample_continuous(continuous_ranges)
        
    else:
        raise ValueError("Cannot sample delay: all provided intervals are empty or invalid.")



def sample_delay(delay_intervals: list[Interval]) -> float:
    """
    Samples a continuous delay from a list of valid intervals.
    Mathematically ensures that continuous ranges strictly dominate isolated discrete points,
    preserving the un-skewed probability density function required for sound SMC.
    """
    discrete_points = []
    continuous_ranges = []

    # 1. Sanitize infinity & categorize intervals
    for interval in delay_intervals:
        safe_upper = interval.upper
        
        if safe_upper == float("inf"):
            # If unbounded, we artificially bound it to an extremely high number for simulation
            safe_upper = max(interval.lower + MAX_TIME_BOUND, MAX_TIME_BOUND)
            is_upper_inclusive = True 
        else:
            is_upper_inclusive = interval.include_upper

        # 2. Check for point intervals vs. continuous ranges
        if interval.lower == safe_upper:
            # It's a point interval (e.g., [5.0, 5.0])
            if interval.include_lower and is_upper_inclusive:
                discrete_points.append(interval.lower)
            else:
                # E.g., (3, 3] or [5, 5). This is a mathematically empty set, ignore it.
                continue
        else:
            # It's a continuous range (e.g., [0.0, 10.0])
            continuous_ranges.append((interval.lower, safe_upper, interval.include_lower, is_upper_inclusive))

    has_discrete = len(discrete_points) > 0
    has_continuous = len(continuous_ranges) > 0

    # 3. The Pure Stochastic Scheduler Logic (The Fix)
    if has_continuous:
        # If ANY continuous ranges exist, they hold 100% of the probability mass (Lebesgue measure > 0).
        # Isolated discrete points have a measure of 0 and are mathematically ignored by the continuous PDF.
        return _sample_continuous(continuous_ranges)
        
    elif has_discrete:
        # If ONLY discrete points exist, the unconstrained delay is a pure discrete distribution.
        # We assume a uniform selection among valid points (resolving action non-determinism in time).
        return random.choice(discrete_points)
        
    else:
        raise ValueError("Cannot sample delay: all provided intervals are empty or mathematically invalid.")


def _sample_continuous(continuous_ranges: list[tuple[float, float, bool, bool]]) -> float:
    """
    Samples uniformly across disjoint continuous intervals, weighting by their length.
    """
    # Calculate the total mathematical length of all valid time
    total_length = sum(upper - lower for lower, upper, inc_l, inc_u in continuous_ranges)
    
    # Draw a single uniform random value across the total valid length
    random_val = random.uniform(0, total_length)

    accumulated = 0.0
    for lower, upper, include_lower, include_upper in continuous_ranges:
        length = upper - lower
        
        # If our random draw falls within this specific chunk
        if random_val <= accumulated + length:
            offset = random_val - accumulated
            sampled_time = lower + offset
            
            # THE EPSILON NUDGE:
            # If the RNG hits the exact boundary, but the boundary is mathematically open/exclusive, 
            # we nudge it by the smallest possible float amount to make it legally valid.
            epsilon = 1e-9 
            
            if sampled_time == lower and not include_lower:
                sampled_time += epsilon
            elif sampled_time == upper and not include_upper:
                sampled_time -= epsilon
                
            return sampled_time
            
        accumulated += length

    # Fallback safety: If floating-point math causes us to overshoot slightly,
    # return the highest possible valid value.
    last_upper, last_include = continuous_ranges[-1][1], continuous_ranges[-1][3]
    return last_upper if last_include else last_upper - 1e-9
