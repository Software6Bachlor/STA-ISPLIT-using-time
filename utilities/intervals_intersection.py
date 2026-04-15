from typing import Optional
from models.interval import Interval

def intervals_intersection(
    intervals_a: list[Interval], 
    intervals_b: list[Interval]
) -> Optional[list[Interval]]:
    """
    Returns a list of overlapping intervals from two sorted lists of intervals.
    Returns None if there is no overlap.
    """
            
    result = []
    i, j = 0, 0
    
    while i < len(intervals_a) and j < len(intervals_b):
        start_a = intervals_a[i].lower
        end_a = intervals_a[i].upper
        start_b = intervals_b[j].lower 
        end_b = intervals_b[j].upper
        
        # Calculate the potential overlapping window
        overlap_start = max(start_a, start_b)
        overlap_end = min(end_a, end_b)
        
        # If it's a valid window, save it
        if overlap_start <= overlap_end:
            interval = Interval()
            if start_a > start_b:
                interval.include_lower = intervals_a[i].include_lower
                interval.lower = start_a
            if start_b > start_a:
                interval.include_lower = intervals_b[j].include_lower
                interval.lower = start_b
            if start_a == start_b:
                interval.include_lower =  intervals_a[i].include_lower and intervals_b[j].include_lower
                interval.lower = start_a

                
            # nået hertil med interval calc upper bound and include.
                
                result.append(interval)

            
            
        # Move the pointer of whichever interval ends first, 
        # because it cannot possibly overlap with anything else.
        if end_a < end_b:
            i += 1
        else:
            j += 1
            
    return result if result else None
