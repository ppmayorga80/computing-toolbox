"""dedup file with dedup function"""


def dedup(data: list) -> list:
    """drop duplicates date while preserving original order"""
    #1. build the initial set of values (optimally for checking uniqueness values)
    unique_values = set()
    #2. build the tuple of unique values and the add operation to the set of unique values
    #   both, [x[0] for x in unique_tuple] & unique_values will contain the same values
    #   but the set element will not guarantee the same input order while the list element does.
    unique_tuple = [(x, unique_values.add(x)) for x in data
                    if x not in unique_values]
    #3. extract the unique values in the same order as the input data and return it
    unique_data = [x[0] for x in unique_tuple]
    return unique_data
