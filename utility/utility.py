def interval_union(primary: list[tuple[float,float]], secondary: list[tuple[float,float]] = None):

    if secondary == None:
         secondary = primary 
         

    new_intervals : list[tuple[float, float]]

    for primary_interval in primary:
        primary.pop()
        overlaps : list[tuple[float, float]]
        #new_overlaps : list[tuple[float, float]]
        overlaps.append(primary_interval)

        for secondary_interval in secondary:
            if primary_interval[0] > secondary_interval[1] or primary_interval[1] < secondary_interval[0]:
            # overlaps
                overlaps.append(secondary_interval)
                secondary.remove(secondary_interval)

    
        #get largest and smallest interval values.
        largest : int = 0
        smallest : int = 0
        for interval in overlaps:
            if interval[0] < smallest:
                smallest = interval[0]

        if interval[1] > largest:
                smallest = interval[1]
        new_intervals.append(tuple[smallest, largest])
    new_intervals.append(secondary)

