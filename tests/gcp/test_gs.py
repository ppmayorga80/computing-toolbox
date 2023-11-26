"""Test Gs class for Google cloud storage"""
from unittest.mock import patch, Mock

from computing_toolbox.gcp.gs import Gs


def raise_error():
    """function that raise an exception"""
    raise ValueError("some error")


def create_blob(path: str) -> Mock:
    _, object_name = Gs.split(path)
    mock_blob = Mock()
    mock_blob.name = object_name
    return mock_blob


class TestGS:
    """Class for testing Gs google cloud storage"""

    def test_split(self):
        """test how to split a gs path"""
        good_path = "gs://hello/world.txt"
        bucket_name, object_name = Gs.split(good_path)
        assert bucket_name and object_name

        bad_path = "/hello/world.txt"
        bucket_name, object_name = Gs.split(bad_path)
        assert not bucket_name and not object_name

    def test_join(self):
        """test how to join parts of a path"""
        path = Gs.join("hello", "world.txt")
        assert path == "gs://hello/world.txt"

        path = Gs.join("gs://hello", "world.txt")
        assert path == "gs://hello/world.txt"

    @patch("computing_toolbox.gcp.gs.smart_open")
    def test_exists(self, mock_smart_open):
        """test if path exists"""
        # for the first two calls, we configure the mock to return True
        mock_smart_open.open.return_value = True

        # OK for a file
        assert Gs.exists("gs://hello/world.txt")
        # OK for a directory ended with /
        assert Gs.exists("gs://hello/")

        # for the last two calls, we configure the mock to raise an error
        mock_smart_open.open.side_effect = raise_error

        # BAD for a non file
        assert not Gs.exists("gs://NO-BUCKET/EXISTS/NOR/FILE.TXT")
        # BAD for a non directory
        assert not Gs.exists("gs://NO-BUCKET/EXISTS")

    @patch("computing_toolbox.gcp.gs.storage")
    def test_list_files(self, mock_storage):
        """test for list_files"""
        # define configuration variables for the testing
        bucket_name = "hello"
        expected_filenames = [
            Gs.join(bucket_name, "world/1.txt"),
            Gs.join(bucket_name, "world/2.txt"),
            Gs.join(bucket_name, "world/3.txt"),
            Gs.join(bucket_name, "world/n.gz"),
        ]

        # define the list of blobs to be mocked
        mock_list_blobs = [create_blob(name) for name in expected_filenames]
        mock_storage.Client.return_value.list_blobs.return_value = mock_list_blobs

        # get list of files without filter
        filenames = [x for x in Gs.list_files("gs://hello")]
        assert filenames == expected_filenames

        # get list of files without filter
        filenames = [
            x for x in Gs.list_files("gs://hello", re_filter=r"\.gz$")
        ]
        assert filenames == expected_filenames[-1:]

    @patch("computing_toolbox.gcp.gs.storage")
    def test_rm(self, mock_storage):
        """test rm files"""
        # 1. test true delete
        # 1.1 mocking the API
        mock_storage.Client.return_value.bucket.return_value.blob.return_value.delete.return_value = True
        # 1.2 test it
        path = "gs://my-bucket/dir1/dir2/file.txt"
        response = Gs.rm(path)
        assert response is True

        # 2. test false delete
        # 2.1 mocking the API causing an exception
        mock_storage.Client.return_value.bucket.return_value.blob.return_value.delete.side_effect = raise_error
        # 1.2 test it
        path = "gs://my-bucket/dir1/dir2/file.txt"
        response = Gs.rm(path)
        assert response is False
