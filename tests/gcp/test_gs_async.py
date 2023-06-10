"""testing the gs_async.py file"""
from unittest.mock import patch

from computing_toolbox.gcp.gs_async import GsAsync


@patch("computing_toolbox.gcp.gs_async.Storage")
def test_exists_true(mock_storage):
    """test existence of files, this case test for True results"""
    mock_storage.return_result = True

    files = ["gs://file/1", "gs://file/2"]
    data = GsAsync.exists(files)
    assert all(data)


@patch("computing_toolbox.gcp.gs_async.Storage")
def test_exists_false(mock_storage):
    """test existence of files, this case test for False results"""
    mock_storage.side_effect = TimeoutError("timeout")

    files = ["gs://file/1", "gs://file/2"]
    data = GsAsync.exists(files)
    assert all(not x for x in data)


@patch("computing_toolbox.gcp.gs_async.Storage")
def test_read_ok(mock_storage):
    """test file reading, this case test for not None results"""
    mock_storage.return_result = True

    files = ["gs://file/1", "gs://file/2"]
    data = GsAsync.read(files)
    assert all(x is not None for x in data)


@patch("computing_toolbox.gcp.gs_async.Storage")
def test_read_bad(mock_storage):
    """test file reading, this case test for None results"""
    mock_storage.side_effect = TimeoutError("timeout")

    files = ["gs://file/1", "gs://file/2"]
    data = GsAsync.read(files)
    assert all(x is None for x in data)


@patch("computing_toolbox.gcp.gs_async.Storage")
def test_write_ok(mock_storage):
    """test file writing, this case test for good results"""
    mock_storage.return_result = True

    files = ["gs://file/1", "gs://file/2"]
    contents = ["hello", "world"]
    data = GsAsync.write(files, contents)
    assert sum(data) >= 2


@patch("computing_toolbox.gcp.gs_async.Storage")
def test_write_bad(mock_storage):
    """test file writing, this case test for bad results"""
    mock_storage.side_effect = ValueError("some error")

    files = ["gs://file/1", "gs://file/2"]
    contents = ["hello", "world"]
    data = GsAsync.write(files, contents)
    assert all(x is None for x in data)
