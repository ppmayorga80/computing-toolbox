"""this algorithm shrink a list to human-readable format"""


def shrink_list_to_interval_string(interval: list[int],
                                   range_separator_fmt: str = "{a}-{b}",
                                   list_separator: str = ", ") -> str:
    """shrink a list of integers to a interval string representation
    Example:
        input: [1,2,3,4,5,10,11,20,30,31,32,33]
        output: "1-5,10-11,20,30-33"
    :param interval: the integer list
    :param range_separator_fmt: the format string to present the range from a to b.
                                Use a and b as the formatted variables
    :param list_separator: the separator string between ranges
    """
    # 1. sort the interval in ascending order
    sorted_intervals = sorted(p for p in interval)
    # 2. set current interval (a:left, b:right) to empty values
    a, b = None, None

    # 3. walk over the interval
    range_intervals = []
    for x in sorted_intervals:
        # 3.1 if current value is next to the previous interval, update the right interval
        if x - 1 == b:
            b = x
        else:
            # 3.2 otherwise, we discover a new interval ∴ add previous interval to the set
            # of shorten intervals, if possible, and then, update current interval
            if a is not None and b is not None:
                range_intervals.append((a, b))
            # 3.3 prepare next interval
            a, b = x, x

    # 4. insert last pending interval
    if a is not None and b is not None:
        range_intervals.append((a, b))

    # 5. compute the shrink interval, map to a comma separated string and return the result
    shrink_intervals = [
        f"{pa}" if pa == pb else range_separator_fmt.format(a=pa, b=pb)
        for pa, pb in range_intervals
    ]
    shrink_intervals_str = list_separator.join(shrink_intervals)

    return shrink_intervals_str


def interval_string_to_shrink_list(interval_string: str,
                                   range_separator: str = "-",
                                   list_separator: str = ",") -> list[int]:
    """given the interval string, this function return a list of expanded int values
    input: '1-3,5-10,15,18-20'
    output: [1,2,3,5,6,7,8,9,10,15,18,19,20]
    """
    # 1. parse the separator string
    sub_interval_strings = [
        x.strip().split(range_separator)
        for x in interval_string.split(list_separator)
    ]
    # 2. check if there are bad separator lists
    bad_format = [1 for x in sub_interval_strings if len(x) > 2]
    if bad_format:
        raise ValueError("Format string must be of the form 'A-B'")
    # 3. parse the range strings
    sub_interval_expanded = [(int(x[0]), int(x[0])) if len(x) == 1 else
                             (int(x[0]), int(x[1]))
                             for x in sub_interval_strings]
    # 4. build the output values
    values = [
        xk for a, b in sub_interval_expanded for xk in list(range(a, b + 1))
    ]

    return values
