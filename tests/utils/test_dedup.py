"""test the dedup function"""
from computing_toolbox.utils.dedup import dedup


def test_dedup():
    """test the dedup function"""
    print("HERE")
    #1. full example
    expected_result = [1, 2, 3, 5, 8, 7, 4, 6, 9]
    x = dedup([1, 1, 2, 3, 5, 8, 2, 3, 5, 7, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    assert x == expected_result

    #2. empty list
    x = dedup([])
    assert isinstance(x, list)
    assert len(x) == 0

    #2. compact
    x = dedup([1] * 100)
    assert x == [1]
