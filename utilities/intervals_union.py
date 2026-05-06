from models.interval import Interval

def intervals_union(*intervals: list[Interval]) -> list[Interval]:
    """
    Takes a list of listed intervals. and returns the union of them.
    Example: [(1,2),(2,3)] = [(1,3)] - Note that intervals also has inclusion booleans on the bounds which are also handled by the function.

    """

    combined_intervals: list[Interval] = [
        interval 
        for range_list in intervals 
        if range_list is not None 
        for interval in range_list
    ]

    # Return if given empty lists
    if not combined_intervals:
        return []

    # Sort intervals based on their start time
    combined_intervals.sort(key=lambda x: (x.lower, not x.include_lower))

    merged: list[Interval] = [combined_intervals[0]]

    for interval in combined_intervals[1:]:
        current_start, current_end = interval.lower, interval.upper
        last_merged_end = merged[-1].upper        
            
        # Since they are sorted by start time, we ONLY need to check if the 
        # current interval starts before the last one ends.        
        if (current_start < last_merged_end) or (current_start == last_merged_end and (interval.include_lower or merged[-1].include_upper)):
            # Overlap found - Merge them
            new_upper = last_merged_end
            new_include_upper = merged[-1].include_upper

            if current_end > last_merged_end:
                new_upper = (current_end)
                new_include_upper = interval.include_upper
            elif current_end == last_merged_end:
                new_include_upper = interval.include_upper or merged[-1].include_upper

            merged[-1] = Interval(
                lower=merged[-1].lower,
                upper=new_upper,
                include_lower=merged[-1].include_lower,
                include_upper=new_include_upper
            )
        
        else:
            # No overlap - The current interval is separate.
            merged.append(interval)
    return merged

