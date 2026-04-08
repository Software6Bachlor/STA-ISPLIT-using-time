from typing import Optional

def intervals_intersection(
    intervals_a: list[tuple[float, float]], 
    intervals_b: list[tuple[float, float]]
) -> Optional[list[tuple[float, float]]]:
    """
    Returns a list of overlapping intervals from two sorted lists of intervals.
    Returns None if there is no overlap.
    """
            
    result = []
    i, j = 0, 0
    
    while i < len(intervals_a) and j < len(intervals_b):
        start_a, end_a = intervals_a[i]
        start_b, end_b = intervals_b[j]
        
        # Calculate the potential overlapping window
        overlap_start = max(start_a, start_b)
        overlap_end = min(end_a, end_b)
        
        # If it's a valid window, save it
        if overlap_start <= overlap_end:
            result.append((overlap_start, overlap_end))
            
        # Move the pointer of whichever interval ends first, 
        # because it cannot possibly overlap with anything else.
        if end_a < end_b:
            i += 1
        else:
            j += 1
            
    return result if result else None