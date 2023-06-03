"""test jsonl file"""
import os
from dataclasses import dataclass
from datetime import date, timedelta

from computing_toolbox.utils.jsonl import Jsonl


def test_write_read_and_count_lines(tmp_path):
    """test how to write, read and count-lines"""

    # A.1 create the list of data
    expected_n: int = 10
    expected_data = [{"k": k + 1, "name": "foo"} for k in range(expected_n)]
    # A.2 define path
    path = str(tmp_path / "counter.jsonl")

    # B. write operation
    # B.1 path shouldn't exist at the beginning
    assert not os.path.exists(path)

    # B.2 execute the write method
    n = Jsonl.write(path, expected_data)

    # B.3 testing
    assert n == expected_n
    assert os.path.exists(path)

    # C. read operation
    # C.1.1 read as jsonl
    data = Jsonl.read(path)
    # C.1.2 testing
    assert data == expected_data
    # C.2 read with offset
    data = Jsonl.read(path, offset=expected_n // 2)
    assert len(data) == expected_n - expected_n // 2

    # D. count lines
    n = Jsonl.count_lines(path)
    assert n == expected_n


@dataclass
class MyCounter:
    k: int
    name: str
    date: date


def today_plus_k(k: int) -> date:
    dt_now = date.today() + timedelta(days=k)
    return dt_now


def test_offset_limit_with_class(tmp_path):
    """test how to write, read and count-lines with offset,limit and mapping class"""

    # A.1 create the list of data
    expected_n: int = 10
    expected_data = [
        MyCounter(k=k + 1, name="foo", date=today_plus_k(k))
        for k in range(expected_n)
    ]
    # A.2 define path
    path = str(tmp_path / "counter.jsonl")

    # B. write, count and read with mapping
    Jsonl.write(path, expected_data, tqdm_kwargs={})
    n_lines = Jsonl.count_lines(path, tqdm_kwargs={})
    data = Jsonl.read(path, mapping_class=MyCounter, limit=n_lines, tqdm_kwargs={})
    assert data == expected_data

    # C. test how to read only 2 elements
    data = Jsonl.read(path,
                      MyCounter,
                      offset=expected_n // 2,
                      limit=2,
                      tqdm_kwargs={})
    assert len(data) == 2
    data_x, data_y = data
    assert data_x.k == 6
    assert data_y.k == 7

    # D. test how to read when reach the end
    # trying to read 4 but only 2 returned
    data = Jsonl.read(path,
                      mapping_class=MyCounter,
                      offset=expected_n - 2,
                      limit=4,
                      tqdm_kwargs={})
    assert len(data) == 2
    data_x, data_y = data
    assert data_x.k == expected_n - 1
    assert data_y.k == expected_n
