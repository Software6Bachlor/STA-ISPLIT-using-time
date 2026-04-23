import random
import math
from models.Interval import Interval

def sample_delay(delay_intervals: list[Interval]) -> float:
    #LASSE NÅET HERTIL - weights når interval er lille? what to do?
    """
    Samples a random time delay from a list of valid, disjoint continuous intervals.
    Uses weighted probability to ensure fair sampling across gaps.
    """
    
    # If any valid window is infinite.
    if any(iv.upper == float('inf') for iv in delay_intervals):
        raise ValueError(f"Staying in a location inf time is not allowed, go intervals: {delay_intervals}")

    # Calculate the weights (lengths) of all intervals
    weights = [iv.upper - iv.lower for iv in delay_intervals]
    total_weight = sum(weights)

    # If all valid times are exact points (e.g., [2.0, 2.0] and [5.0, 5.0]), 
    if total_weight == 0:
        chosen_interval = random.choice(delay_intervals)
        return chosen_interval.lower

    # random.choices picks one interval based on its size. 
    # (e.g., a 10-second window is 5x more likely to be picked than a 2-second window)
    chosen_interval = random.choices(delay_intervals, weights=weights, k=1)[0]

    # 5. Sample inside the winning interval
    lower = chosen_interval.lower
    upper = chosen_interval.upper
    delay = random.uniform(lower, upper)
    
    # Reroll if we hit an exclusive boundary
    while (not chosen_interval.include_lower and delay == lower) or \
          (not chosen_interval.include_upper and delay == upper):
        delay = random.uniform(lower, upper)
        
    return delay