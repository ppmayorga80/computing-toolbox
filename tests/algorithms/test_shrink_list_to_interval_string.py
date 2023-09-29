"""Testing parallel functions"""

from computing_toolbox.algorithms.shrink_list_to_interval_string import shrink_list_to_interval_string


def test_shrink_list_to_interval_string():
    """Test shrink_list_to_interval_string function"""
    # 1. prepare the lists to test and the expected results
    lists_to_test = [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 50, 51, 52, 53],
                     [1, 3, 5, 7, 9], [11, 12, 13, 14, 15],
                     [20, 21, 22, 23, 50]]
    expected_results = [
        "1-10, 20, 50-53", "1, 3, 5, 7, 9", "11-15", "20-23, 50"
    ]

    # 2. test for every list in the set
    for the_list, expected_result in zip(lists_to_test, expected_results):
        # 2.1 compute the result and test it
        result = shrink_list_to_interval_string(the_list)
        assert result == expected_result
