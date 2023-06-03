"""Testing parallel functions"""
import pytest

from computing_toolbox.algorithms.split_range import split_range, split_range_ab


def test_split_range():
    """Test split function"""

    # test for non-positive values of n
    for n in range(-3, 1):
        with pytest.raises(ValueError):
            split_range(n, parts=10)

    # test for non-positive values of parts
    for m in range(-3, 1):
        with pytest.raises(ValueError):
            split_range(n=10, parts=m)

    # test for different values of parts with a fixed n
    n = 100
    for m in range(1, 11):
        intervals = split_range(n, parts=m)
        # 1. test interval length
        assert len(intervals) == m
        # 2. test if interval values are continuous
        a_0, b_0 = intervals[0]
        assert (a_0 == 0) and (b_0 > 0)
        for a, b in intervals[1:]:
            assert a == b_0
            a_0, b_0 = a, b
        # 3. test if the interval ends with n
        assert b_0 == n


def test_split_range_ab():
    """test split range with arbitrary interval [a,b)"""
    x = split_range_ab(13, 29, 3)  # [13,29) ÷ 3
    assert x == [(13, 19), (19, 24), (24, 29)]

    x = split_range_ab(13, 33, 2)  # [13,29) ÷ 3
    assert x == [(13, 23), (23, 33)]
