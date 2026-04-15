from models.interval import interval

def intervals_negated(intervals: list[interval]) -> list[interval]:
    output = []
    i = 0
    if intervals == None:
        return [interval(0, float("inf"), True, True)]
    
    if intervals[0][0] != 0:
        output.append(interval(0, intervals[0].lower, True, not intervals[0].include_upper))
        i += 1

    for i in range(i, len(intervals)-2):
        output.append(interval(intervals[i].upper, intervals[i+1].lower, not intervals[i].include_upper, not intervals[i+1].include_lower))

    if intervals[-1].upper != float("inf"):
        output.append(interval(intervals[-1].upper, float("inf"), not intervals[-1].include_upper, True))

    if output == []:
         return None
    else:
        return output




