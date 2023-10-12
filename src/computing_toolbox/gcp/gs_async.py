"""Google Storage class with async operations"""
import asyncio
import gzip

from gcloud.aio.storage import Storage
from tqdm import tqdm

from computing_toolbox.gcp.gs import Gs


class GsAsync:
    """GS async class
    if you want to read/write gzip files you only need to provide *.gz extension in the path

    example 1:
        response = GsAsync.write(["gs://b1/f1.txt.gz"],["hello, world"])
    in the previous example the text "hello, world" will be compressed before save to the file='gs://b1/f2.txt.gz'

    example 2:
        response = GsAsync.read(["gs://b1/f1.txt.gz"])
    in the previous example, response[0] contains the string content (uncompressed) in the file='gs://b1/f1.txt'
    i.e. response[0]=="hello, world"

    """

    # default timeout for read and write operations
    DEFAULT_TIMEOUT: int = 3600

    @classmethod
    async def _exist_one(cls,
                         path: str,
                         timeout: int,
                         tqdm_pbar: tqdm or None = None) -> bool:
        """async function for testing existence of one file

        :param path: storage path
        :param timeout: timeout to trigger an error
        :param tqdm_pbar: a default progressbar
        :return: True if path exists
        """
        # 1. get bucket and object
        bucket, key = Gs.split(path)

        # 2. try to read file metadata
        try:
            async with Storage() as client:
                _ = await client.download_metadata(bucket,
                                                   key,
                                                   timeout=timeout)
                # 2.1 if success mark as True
                flag = True
        except Exception:
            # 2.2 if fails mark as False
            flag = False

        # update the progress bar if exists
        _ = tqdm_pbar.update() if tqdm_pbar else None

        return flag

    @classmethod
    async def _exist_many(cls,
                          paths: list[str],
                          timeout: int,
                          tqdm_pbar: tqdm or None = None) -> list[bool]:
        """test for existence of many files

        :param paths: list of storage paths
        :param timeout: timeout before trigger an error
        :param tqdm_pbar: progress bar
        :return: the list of flags
        """
        # 1. create the list of functions to call
        tasks = [
            asyncio.ensure_future(cls._exist_one(f, timeout, tqdm_pbar))
            for f in paths
        ]
        # 2. execute all functions at once
        results = await asyncio.gather(*tasks)
        # 3. return the results
        return results

    @classmethod
    def exists(cls,
               paths: list[str],
               batch_size: int = 50,
               timeout: int or None = None,
               tqdm_kwargs: dict or None = None) -> list[bool]:
        """wrapper that calls async function that test for path existences

        :param paths: the list of paths
        :param batch_size: process the async operation in batches of this size
        :param timeout: timeout, set as DEFAULT_TIMEOUT if None (default: None)
        :param tqdm_kwargs: if not None, define a tqdm progress bar (default: None)
        :return: the list of flags
        """
        # 1. define the timeout
        timeout = timeout if timeout else cls.DEFAULT_TIMEOUT

        batch_tqdm_kwargs = {
            **{
                "desc": f"GsAsync.exists {len(paths)} paths in batches",
                "position": 0,
                "leave": True
            },
            **tqdm_kwargs
        } if tqdm_kwargs is not None else tqdm_kwargs
        batch_range = range(0, len(paths), batch_size)
        batch_counter = tqdm(
            batch_range, **
            batch_tqdm_kwargs) if tqdm_kwargs is not None else batch_range

        responses = []
        for k in batch_counter:
            batch_paths = paths[k:k + batch_size]
            # 2. define progress bar kwargs
            async_tqdm_kwargs = {
                **{
                    "desc": "GsAsync.exists",
                    "total": len(batch_paths),
                    "position": 1,
                    "leave": False
                }
            } if tqdm_kwargs is not None else tqdm_kwargs
            # 2.1 define the progressbar
            tqdm_pbar = tqdm(
                range(len(batch_paths)), **
                async_tqdm_kwargs) if async_tqdm_kwargs is not None else None
            partial_response = asyncio.run(
                cls._exist_many(batch_paths, timeout, tqdm_pbar))

            # 3. save the async execution
            responses += partial_response

        return responses

    @classmethod
    async def _read_one(cls,
                        path: str,
                        timeout: int,
                        tqdm_pbar: tqdm or None = None) -> str or None:
        """read one path asynchronously

        :param path: path to be read
        :param timeout: timeout before to raise an exception
        :param tqdm_pbar: the progressbar (default: None)
        :return: path content
        """
        # 1. get bucket and key
        bucket, key = Gs.split(path)

        # 2. try to read the content in bytes
        try:
            async with Storage() as client:
                content_in_bytes: bytes = await client.download(
                    bucket, key, timeout=timeout)
                # 2.1 parse zip content if needed
                content_in_bytes = gzip.decompress(
                    content_in_bytes) if path.endswith(
                        ".gz") else content_in_bytes

                # 2.2 if success, convert to string.
                content = content_in_bytes.decode("utf8")
        except Exception:
            # 2.2 if fails, set content to None
            content = None

        # 3. update progressbar if defined
        _ = tqdm_pbar.update() if tqdm_pbar else None

        # 4. return the content
        return content

    @classmethod
    async def _read_many(cls,
                         paths: list[str],
                         timeout: int,
                         tqdm_pbar: tqdm or None = None) -> list[str]:
        """read many paths asynchronously

        :param paths: the list of paths
        :param timeout: timeout before trigger an error
        :param tqdm_pbar: the progressbar (default: None)
        :return: the list of contents
        """
        # 1. define the list of functions to call
        tasks = [
            asyncio.ensure_future(cls._read_one(f, timeout, tqdm_pbar))
            for f in paths
        ]
        # 2. call all the functions
        results = await asyncio.gather(*tasks)
        # 3. return the results
        return results

    @classmethod
    def read(cls,
             paths: list[str],
             batch_size: int = 10,
             timeout: int or None = None,
             tqdm_kwargs: dict or None = None) -> list[str]:
        """wrapper function that calls the async version of read_many

        :param paths: the list of paths
        :param batch_size: the number of batch operations to split the async read operation
        :param timeout: timeout before raise an exception, if None set as DEFAULT_TIMEOUT (default: None)
        :param tqdm_kwargs: if not None define a progressbar, set {} for a default progressbar (default: None)
        :return: the list of contents
        """
        # 1. define the timeout
        timeout = timeout if timeout else cls.DEFAULT_TIMEOUT

        results = []
        for k in tqdm(range(0, len(paths), batch_size),
                      desc=f"async read batch_size={batch_size}",
                      position=0,
                      leave=True):
            # 2.1 define the subset
            path_subset = paths[k:k + batch_size]
            subset_len = len(path_subset)
            # 2.2 define the progressbar kwargs
            tqdm_kwargs_subset = {
                **{
                    "desc": "GsAsync.read",
                    "total": subset_len,
                    "position": 1,
                    "leave": False
                },
                **tqdm_kwargs
            } if tqdm_kwargs is not None else tqdm_kwargs
            n_it = range(subset_len)
            tqdm_pbar = None if tqdm_kwargs_subset is None else tqdm(
                n_it, **tqdm_kwargs_subset)

            # 2.3 call the async method and update the results
            result_subset = asyncio.run(
                cls._read_many(path_subset, timeout, tqdm_pbar))
            results += result_subset

        # 3. return the results
        return results

    @classmethod
    async def _write_one(cls,
                         path: str,
                         content: str,
                         timeout: int,
                         tqdm_pbar: tqdm or None = None) -> int or None:
        """async function to write content to a path

        :param path: the storage path
        :param content: the content to be written
        :param timeout: timeout before to raise an exception
        :param tqdm_pbar: a progressbar
        :return: the number of bytes written
        """
        # 1. get the bucket and key
        bucket, key = Gs.split(path)

        # 2. try to write the content
        try:
            content = gzip.compress(
                content.encode("utf8")) if path.endswith(".gz") else content
            async with Storage() as client:
                response = await client.upload(bucket,
                                               key,
                                               content,
                                               timeout=timeout)
                # 2.1 if success get the number of bytes written
                n_bytes = int(response["size"])
        except Exception:
            # 2.2 if fails, set n_bytes to None
            n_bytes = None

        # 3. update progressbar if defined
        _ = tqdm_pbar.update() if tqdm_pbar else None

        # 4. return the number of bytes written
        return n_bytes

    @classmethod
    async def _write_many(cls,
                          paths: list[str],
                          contents: list[str],
                          timeout: int,
                          tqdm_pbar: tqdm or None = None) -> list[int]:
        """function to write many files

        :param paths: the list of paths
        :param contents: corresponding content list to be wrriten
        :param timeout: timeout before to raise an exception
        :param tqdm_pbar: the progressbar
        :return: the list of bytes written
        """
        # 1. define the function to call
        tasks = [
            asyncio.ensure_future(cls._write_one(f, s, timeout, tqdm_pbar))
            for f, s in zip(paths, contents)
        ]
        # 2. execute all the function asynchronously
        results = await asyncio.gather(*tasks)
        # 3. return the results
        return results

    @classmethod
    def write(cls,
              paths: list[str],
              contents: list[str],
              batch_size: int = 10,
              timeout: int or None = None,
              tqdm_kwargs: dict or None = None) -> list[int]:
        """wrapper to the async version of write_many

        :param paths: the list of paths
        :param contents: corresponding content list to be wrriten
        :param batch_size: process write operations in batches of this size,
        :param timeout: timeout before to raise an exception
        :param tqdm_kwargs: if defined, at least {}, creates a progressbar
                able to track the writing operation (default: None)
        :return: the list of bytes written
        """
        # 1. define the timeout
        timeout = timeout if timeout else cls.DEFAULT_TIMEOUT

        # 2. walk over the paths in chunks
        results = []
        for k in tqdm(range(0, len(paths), batch_size),
                      desc=f"async write batch_size={batch_size}",
                      position=0,
                      leave=True):
            # 2.1 define the subset
            path_subset = paths[k:k + batch_size]
            content_subset = contents[k:k + batch_size]
            subset_len = len(path_subset)
            # 2.2 define the progressbar kwargs
            tqdm_kwargs_subset = {
                **{
                    "desc": "GsAsync.write",
                    "total": subset_len,
                    "position": 1,
                    "leave": False
                },
                **tqdm_kwargs
            } if tqdm_kwargs is not None else tqdm_kwargs
            n_it = range(subset_len)
            tqdm_pbar = None if tqdm_kwargs_subset is None else tqdm(
                n_it, **tqdm_kwargs_subset)

            # 2.3 call the async method and update the results
            result_subset = asyncio.run(
                cls._write_many(path_subset, content_subset, timeout,
                                tqdm_pbar))
            results += result_subset

        # 3. return the results
        return results
