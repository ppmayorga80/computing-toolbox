"""test jsonl file"""
import json
import os
from dataclasses import dataclass, asdict
from datetime import date, timedelta
from unittest.mock import patch

import jsons

from computing_toolbox.utils.jsonl import Jsonl, _jsonl_parse_one_line, _jsonl_dumps_one_object, _split_str, \
    _parse_documents


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
    data = Jsonl.read(path,
                      mapping_class=MyCounter,
                      limit=n_lines,
                      tqdm_kwargs={})
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


def test__jsonl_parse_one_line():
    expected_data = MyCounter(k=66, name="foo", date=date.today())
    expected_data_as_str = jsons.dumps(asdict(expected_data))
    data = _jsonl_parse_one_line((expected_data_as_str, MyCounter))
    assert isinstance(data, MyCounter)
    assert data == expected_data


def test_parallel_read():
    """test parallel read"""
    path = os.path.join(os.path.dirname(__file__),
                        "prime-numbers-up-to-20.jsonl")
    numbers1 = Jsonl.parallel_read(path=path)
    numbers2 = Jsonl.parallel_read(path=path, tqdm_kwargs={})
    assert numbers1 == numbers2
    assert isinstance(numbers1, list)
    assert len(numbers1) == 8


def test_dumps_one_object():
    """test the function used in parallel write"""
    data = {"name": "foo", "value": "bar", "n": 10}
    line = _jsonl_dumps_one_object(data)
    assert line == json.dumps(data)


def test_parallel_write(tmp_path):
    """test parallel write"""
    path = str(tmp_path / "fibonacci-numbers-up-to-20.jsonl")
    fibs = [{
        "position": 1,
        "value": 1
    }, {
        "position": 2,
        "value": 1
    }, {
        "position": 3,
        "value": 2
    }, {
        "position": 4,
        "value": 3
    }, {
        "position": 5,
        "value": 5
    }, {
        "position": 6,
        "value": 8
    }, {
        "position": 7,
        "value": 13
    }]

    assert not os.path.exists(path)
    n_bytes = Jsonl.parallel_write(path=path, data=fibs, tqdm_kwargs={})
    assert os.path.exists(path)
    assert n_bytes > 0
    data = Jsonl.read(path)
    assert data == fibs

    n_bytes = Jsonl.parallel_write(path=path, data=fibs)
    assert os.path.exists(path)
    assert n_bytes > 0
    data = Jsonl.read(path)
    assert data == fibs


def test_split_str():
    """test the _split_str method"""
    content = "hello\nworld"
    lines = _split_str(content)
    assert lines == ["hello", "world"]


def test_parse_document():
    """test the parse_document method"""
    lines = ['{"name":"hello"}', '{"name":"world"}']
    documents = _parse_documents(lines)
    assert len(documents) == 2
    assert documents[0] == {"name": "hello"}
    assert documents[1] == {"name": "world"}


@patch('computing_toolbox.utils.jsonl.Pool')
@patch("computing_toolbox.utils.jsonl.GsAsync.read")
def test_async_read_no_tqdm(async_read_mock, pool_mock):
    """test async read method"""
    # 1. load documents for testing
    # 1.1 get local paths
    local_paths = [
        os.path.join(os.path.dirname(__file__),
                     "prime-numbers-up-to-20.jsonl"),
        os.path.join(os.path.dirname(__file__),
                     "fibonacci-numbers-up-to-20.jsonl")
    ]
    # 1.2 read content strings
    raw_contents = []
    for path in local_paths:
        with open(path, "r", encoding="utf8") as fp:
            content = fp.read()
        raw_contents.append(content)
    # 1.3 split contents by lines
    raw_lines = [x.split("\n") for x in raw_contents]
    # 1.4 expected documents
    expected_documents = [[json.loads(xk) for xk in x] for x in raw_lines]
    # 1.5 mock the async read method with the raw contents
    async_read_mock.return_value = raw_contents
    # 1.6 mock the multiprocessing Pool.map with a) raw_lines and b) dictionary documents
    pool_mock.return_value.__enter__.return_value.map.side_effect = [
        raw_lines, expected_documents
    ]
    # 1.7 define what we expect from documents
    primes = [x["value"] for x in expected_documents[0]]
    fibos = [x["value"] for x in expected_documents[1]]

    # 2. define some unreal cloud paths
    paths = [
        "gs://my/bucket/json/primes/prime-numbers-up-to-20.jsonl",
        "gs://my/bucket/json/fibonacci/fibonacci-numbers-up-to-20.jsonl"
    ]

    # 3. perform async_read
    documents = Jsonl.async_read(paths)
    # 3.1 test if we read 2 paths
    assert len(documents) == len(paths)
    # 3.2 test if we have the list of primes in the first document
    assert isinstance(documents[0], list)
    assert len(documents[0]) == len(primes)
    assert all(xk == fk
               for xk, fk in zip(primes, [a["value"] for a in documents[0]]))
    # 3.3 test if we have the list of fibonacci's in the second document
    assert isinstance(documents[1], list)
    assert len(documents[1]) == len(fibos)
    assert all(yk == fk
               for yk, fk in zip(fibos, [a["value"] for a in documents[1]]))


@patch('computing_toolbox.utils.jsonl.Pool')
@patch("computing_toolbox.utils.jsonl.GsAsync.read")
def test_async_read_with_tqdm(async_read_mock, pool_mock):
    """test async read method"""
    # 1. load documents for testing
    # 1.1 get local paths
    local_paths = [
        os.path.join(os.path.dirname(__file__),
                     "prime-numbers-up-to-20.jsonl"),
        os.path.join(os.path.dirname(__file__),
                     "fibonacci-numbers-up-to-20.jsonl")
    ]
    # 1.2 read content strings
    raw_contents = []
    for path in local_paths:
        with open(path, "r", encoding="utf8") as fp:
            content = fp.read()
        raw_contents.append(content)
    # 1.3 split contents by lines
    raw_lines = [x.split("\n") for x in raw_contents]
    # 1.4 expected documents
    expected_documents = [[json.loads(xk) for xk in x] for x in raw_lines]
    # 1.5 mock the async read method with the raw contents
    async_read_mock.return_value = raw_contents
    # 1.6 mock the multiprocessing Pool.map with a) raw_lines and b) dictionary documents
    pool_mock.return_value.__enter__.return_value.imap.side_effect = [
        raw_lines, expected_documents
    ]
    # 1.7 define what we expect from documents
    primes = [x["value"] for x in expected_documents[0]]
    fibos = [x["value"] for x in expected_documents[1]]

    # 2. define some unreal cloud paths
    paths = [
        "gs://my/bucket/json/primes/prime-numbers-up-to-20.jsonl",
        "gs://my/bucket/json/fibonacci/fibonacci-numbers-up-to-20.jsonl"
    ]

    # 3. perform async_read
    documents = Jsonl.async_read(paths, tqdm_kwargs={})
    # 3.1 test if we read 2 paths
    assert len(documents) == len(paths)
    # 3.2 test if we have the list of primes in the first document
    assert isinstance(documents[0], list)
    assert len(documents[0]) == len(primes)
    assert all(xk == fk
               for xk, fk in zip(primes, [a["value"] for a in documents[0]]))
    # 3.3 test if we have the list of fibonacci's in the second document
    assert isinstance(documents[1], list)
    assert len(documents[1]) == len(fibos)
    assert all(yk == fk
               for yk, fk in zip(fibos, [a["value"] for a in documents[1]]))
