
def intervals_union(*intervals: list[tuple[float, float]]) -> list[tuple[float, float]]:

    combined_intervals: list[tuple[float, float]] = [
        interval for range_list in intervals for interval in range_list
    ]

    # Sort intervals based on their start time
    combined_intervals.sort(key=lambda x: x[0])

    merged: list[tuple[float, float]] = [combined_intervals[0]]


    for current_start, current_end in combined_intervals[1:]:
        last_merged_start, last_merged_end = merged[-1]

        # Since they are sorted by start time, we ONLY need to check if the 
        # current interval starts before the last one ends.
        if current_start <= last_merged_end:
            # Overlap found - Merge them
            merged[-1] = (last_merged_start, max(last_merged_end, current_end))
        else:
            # No overlap - The current interval is separate.
            merged.append((current_start, current_end))
    return merged


