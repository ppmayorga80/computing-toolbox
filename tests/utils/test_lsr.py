"""test the lsr.py file"""
import os.path
import types

from computing_toolbox.utils.lsr import lsr


def test_lsr():
    """test lsr funtion"""
    # 1. test 1: generate a generator object with filter
    gen = lsr(os.path.dirname(__file__), r"\.jsonl$", tqdm_kwargs={})
    assert isinstance(gen, types.GeneratorType)
    paths = list(gen)
    assert len(paths) > 0

    # 2. test 2: test a simple generator
    paths = list(lsr(os.path.dirname(__file__), r"\.jsonl$"))
    assert isinstance(paths, list)
    assert all(isinstance(x, str) for x in paths)
    assert len(paths) > 0
