"""test classical tic, toc functions"""
from computing_toolbox.utils.tictoc import tic, toc


def test_tictoc():
    """test tic and toc function with all verbose combinations"""
    for verbose1, verbose2 in [(False, False), (False, True), (True, False),
                               (True, True)]:
        tic(verbose=verbose1)
        _ = [1 + 2 * 3 for _ in range(100)]
        elapsed_time = toc(verbose=verbose2)
        assert elapsed_time > 0
