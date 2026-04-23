from typing import Optional
from models.Interval import Interval

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
       
        interval: Interval = Interval(0,0,False, False)
        if start_a > start_b:
            interval.include_lower = intervals_a[i].include_lower
            interval.lower = start_a
        elif start_b > start_a:
            interval.include_lower = intervals_b[j].include_lower
            interval.lower = start_b
        elif start_a == start_b:
            interval.include_lower =  intervals_a[i].include_lower and intervals_b[j].include_lower
            interval.lower = start_a

        if end_a < end_b:
            interval.upper = end_a
            interval.include_upper = intervals_a[i].include_upper
        elif end_b < end_a:
            interval.upper = end_b
            interval.include_upper = intervals_b[j].include_upper
        else:
            interval.upper = end_a
            interval.include_upper = intervals_a[i].include_upper and intervals_b[j].include_upper
            
        is_valid: bool = (interval.upper > interval.lower) or (interval.upper == interval.lower and interval.include_lower and interval.include_upper)
                
        if is_valid:                
            result.append(interval)
            
        # Move the pointer of whichever interval ends first, 
        if end_a < end_b:
            i += 1
        elif end_b < end_a:
            j += 1
        else:
            if intervals_a[i].include_upper and not intervals_b[j].include_upper:
                j += 1
            elif not intervals_a[i].include_upper and intervals_b[j].include_upper:
                i += 1
            else:
                j += 1
                i += 1
            
    return result if result else None

