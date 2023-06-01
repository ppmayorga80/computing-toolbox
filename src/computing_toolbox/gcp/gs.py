"""Handle file operations in Google Cloud Storage or GS"""
import os
import re
from typing import Sequence

import smart_open
from google.cloud import storage


class Gs:
    """Google Storage class"""
    RE_SPLIT_PATTERN = re.compile(r"^gs://([^/]*)/?(.*)$")

    @classmethod
    def split(cls, path: str) -> tuple[str, str]:
        response = cls.RE_SPLIT_PATTERN.findall(path)
        bucket_name, object_name = "", ""
        if response:
            bucket_name, object_name = response[0]
        return bucket_name, object_name

    @classmethod
    def join(cls, *args) -> str:
        """join several paths and dirs"""
        path = os.path.join(*args)
        if not path.startswith("gs://"):
            path = f"gs://{path}"
        return path

    @classmethod
    def exists(cls, path: str) -> bool:
        """Test if a file or directory exists in Google Cloud Storage
        if path is a directory make sure to write a '/' at the end of `path`

        """
        try:
            _ = smart_open.open(path)
            return True
        except Exception:
            return False

    @classmethod
    def list_files(cls, path: str, re_filter: str = r".*") -> Sequence[str]:
        """Given a path and a regex filter, list all files/dirs that match the filter

        :param path: the initial path where we start the search
        :param re_filter: a regular expression string in raw format, empty string means no filter (default: )
        :return: an iterator that walk over the files within `path` matching the `re_filter`
        """
        # compute the bucket and object names
        bucket_name, object_name = cls.split(path)
        # define if we have a regex function
        re_filter_fn = re.compile(re_filter)

        # 1. walk over all objects within the path in the form (bucket_name,object_name)
        client = storage.Client()
        for blob in client.list_blobs(bucket_name, prefix=object_name):
            # 1.1 build the filename
            filename = cls.join(bucket_name, blob.name)
            # 1.2 decide if we have a regex function
            # 1.2.1 if so, yield only the filename that pass the regex filter
            if re_filter_fn.findall(filename):
                yield filename
