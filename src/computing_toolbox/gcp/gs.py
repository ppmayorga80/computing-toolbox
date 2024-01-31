"""Handle file operations in Google Cloud Storage or GS"""
import os
import re
from itertools import count
from typing import Sequence

import smart_open
from google.cloud import storage
from tqdm import tqdm


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
    def list_files(cls,
                   path: str,
                   re_filter: str = r".*",
                   tqdm_kwargs: dict or None = None) -> Sequence[str]:
        """Given a path and a regex filter, list all files/dirs that match the filter

        :param path: the initial path where we start the search
        :param re_filter: a regular expression string in raw format (default: r".*")
        :param tqdm_kwargs: if defined, at least {}, will create a progressbar with those parameters (default: None)
        :return: iterator that walk over the files within `path` matching the `re_filter`
        """
        # compute the bucket and object names
        bucket_name, object_name = cls.split(path)
        # define if we have a regex function
        re_filter_fn = re.compile(re_filter)

        client = storage.Client()

        tqdm_kwargs = {
            **{
                "desc": "Listing"
            },
            **tqdm_kwargs
        } if tqdm_kwargs is not None else tqdm_kwargs
        blob_pbar_it = tqdm(count(), **
                            tqdm_kwargs) if tqdm_kwargs is not None else None

        # 1. walk over all objects within the path in the form (bucket_name,object_name)
        success = 0
        for blob in client.list_blobs(bucket_name, prefix=object_name):
            _ = blob_pbar_it.update() if blob_pbar_it else None

            # 1.1 build the filename
            filename = cls.join(bucket_name, blob.name)
            # 1.2 decide if we have a regex function
            # 1.2.1 if so, yield only the filename that pass the regex filter
            if re_filter_fn.findall(filename):
                success += 1
                _ = blob_pbar_it.set_postfix_str(
                    f"🟢x{success}") if blob_pbar_it else None
                yield filename

    @classmethod
    def rm(cls, path: str) -> bool:
        """remove an object from gcp"""
        bucket_name, blob_name = cls.split(path)

        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.delete()
            return True
        except Exception:
            pass
        return False
