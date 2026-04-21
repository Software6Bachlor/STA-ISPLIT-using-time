from models.interval import Interval

def intervals_negated(intervals: list[Interval]) -> list[Interval]:
    """
    Takes a list of listed intervals, and returns in negation of it:
    Example: ¬[(1,2)] = [(0,1),(2,inf)] - note intervals also has inclusion booleans on the bounds which are also handled by function.
    """
    output = []
    i = 0
    if intervals == None:
        return [Interval(0, float("inf"), True, True)]
    
    if intervals[0].lower != 0:
        output.append(Interval(0, intervals[0].lower, True, not intervals[0].include_lower))
        i += 1

    for i in range(i, len(intervals)-2):
        output.append(Interval(intervals[i].upper, intervals[i+1].lower, not intervals[i].include_upper, not intervals[i+1].include_lower))

    if intervals[-1].upper != float("inf"):
        output.append(Interval(intervals[-1].upper, float("inf"), not intervals[-1].include_upper, True))

    if output == []:
         return None
    else:
        return output




