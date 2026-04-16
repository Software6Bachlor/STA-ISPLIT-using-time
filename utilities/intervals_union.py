from models.interval import Interval

def intervals_union(*intervals: list[Interval]) -> list[Interval]:

    combined_intervals: list[Interval] = [
        interval for range_list in intervals for interval in range_list
    ]

    # Sort intervals based on their start time
    combined_intervals.sort(key=lambda x: (x.lower, not x.include_lower))

    merged: list[Interval] = [combined_intervals[0]]


    for interval in combined_intervals[1:]:
        current_start, current_end = interval.lower, interval.upper
        last_merged_start, last_merged_end = merged[-1].lower, merged[-1].upper

        # Since they are sorted by start time, we ONLY need to check if the 
        # current interval starts before the last one ends.

        
        if (current_start < last_merged_end) or (current_start == last_merged_end and (interval.include_lower or merged[-1].include_upper)):
            # Overlap found - Merge them
            merged[-1] = (last_merged_start, max(last_merged_end, current_end))
        else:
            # No overlap - The current interval is separate.
            merged.append((current_start, current_end))
    return merged


