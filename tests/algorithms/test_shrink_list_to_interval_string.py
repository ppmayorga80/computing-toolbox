"""Testing parallel functions"""
import pytest

from computing_toolbox.algorithms.shrink_list_to_interval_string import shrink_list_to_interval_string, \
    interval_string_to_shrink_list


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


def test_interval_string_to_shrink_list():
    """test the function interval_string_to_shrink_list"""
    # 1. test a good list
    # 1.1 define the input and the expected output
    text1 = '1-3,8,10-15'
    expected_output = [1, 2, 3, 8, 10, 11, 12, 13, 14, 15]
    # 1.2 call the function
    output = interval_string_to_shrink_list(interval_string=text1)
    # 1.3 test if it works as we expected
    assert output == expected_output

    # 2. call the function with two of the possible errors
    # 2.1 more than 2 intervals
    # 2.2 with no integer values
    with pytest.raises(ValueError) as _:
        _ = interval_string_to_shrink_list("1-10-20,50-100")
        _ = interval_string_to_shrink_list("1-10,50x,100x")
