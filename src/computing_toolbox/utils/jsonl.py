"""json line library
to handle read and write operations on local and cloud files
in both format: plain or compressed (gzip)
"""
import logging
from multiprocessing import cpu_count, Pool
from itertools import count
from typing import Any

import json
import jsons
import smart_open
from tqdm import tqdm

from computing_toolbox.gcp.gs_async import GsAsync


def _jsonl_parse_one_line(args):
    """parse one line at a time"""
    line, mapping_class = args
    document = jsons.loads(line, cls=mapping_class)
    return document


def _jsonl_dumps_one_object(args):
    """dumps one object at a time"""
    x = args
    line = jsons.dumps(x)
    return line


def _split_str(args):
    """split string"""
    text = args
    lines = text.split('\n') if text else []
    return lines


def _parse_documents(args):
    """split string"""
    lines = args
    documents = [json.loads(line) for line in lines]
    return documents


class Jsonl:
    """class that concentrates common json line operations"""

    @classmethod
    def count_lines(cls, path: str, tqdm_kwargs: dict or None = None) -> int:
        """count the number of lines if the path provided

        :param path: the file path to be read
        :param tqdm_kwargs: if provided (at least {}) define a tqdm progress bar (default: None)
        :return: the number of lines in the file
        """
        # 1. compute tqdm_kwargs
        tqdm_kwargs = {
            **{
                "desc": f"count_lines('{path})'"
            },
            **tqdm_kwargs
        } if tqdm_kwargs is not None else tqdm_kwargs
        # 2. open the file
        with smart_open.open(path) as fp:
            # 2.1 define the file iterator
            fp_iterator = tqdm(fp, **
                               tqdm_kwargs) if tqdm_kwargs is not None else fp
            # 2.2 count the number of lines
            n_lines = len([1 for _ in fp_iterator])
        return n_lines

    @classmethod
    def read(cls,
             path: str,
             mapping_class: Any = None,
             offset: int = 0,
             limit: int or None = None,
             tqdm_kwargs: dict or None = None) -> list[dict]:
        """read a json line file
        if provided offset and/or limit, this method jumps the first `offset` lines
        and only return (at most) `limit` number of objects mapping to a given class `mapping_class`
        if provided.

        :param path: path to the file to be read
        :param mapping_class: class to apply to every read line (default: None)
        :param offset: skip the first `offset` lines (default: 0)
        :param limit: if provided, return at most `limit` objects (default: None)
        :param tqdm_kwargs: if provided (at least {}) define a tqdm progress bar with those parameters (default: None)
        :return: the list of json objects
        """
        # 1. define tqdm_kwargs for skip and read loops
        tqdm_skip_kwargs = {
            **{
                "desc": f"jsonl_skip('{path}')",
                "total": offset
            },
            **tqdm_kwargs
        } if tqdm_kwargs is not None else tqdm_kwargs
        tqdm_read_kwargs = {
            **{
                "desc": f"jsonl_read('{path}')",
                "total": limit
            },
            **tqdm_kwargs
        } if tqdm_kwargs is not None else tqdm_kwargs

        # 2. open the file
        with smart_open.open(path) as fp:
            # 2.1 skipping the first offset lines
            if offset:
                # define the iterator and skip those lines
                skip_iterator = tqdm(
                    range(offset), **tqdm_skip_kwargs
                ) if tqdm_skip_kwargs is not None else range(offset)
                _ = [_ for _, _ in zip(skip_iterator, fp)]

            # 2.2 define the read iterator
            limit_iterator = count() if limit is None else range(limit)
            tqdm_limit_iterator = tqdm(
                limit_iterator, **tqdm_read_kwargs
            ) if tqdm_read_kwargs is not None else limit_iterator

            # 2.3 read the limit number of lines at most
            # 2.4 read the data and transforms to object
            data = [
                jsons.loads(line_k, mapping_class)
                for _, line_k in zip(tqdm_limit_iterator, fp)
            ]

        return data

    @classmethod
    def write(cls,
              path: str,
              data: list[dict or object],
              append_mode: bool = False,
              tqdm_kwargs: dict or None = None) -> int:
        """write a json line file
        converting every dict in data to a string and send it to the file.

        if append_mode is True and the path exists, the data will be appended to the end
        otherwise the file will be replaced with the content in data.
        In other words, if append_mode==False, then, the open function is called
        with mode="w"; if append_mode==True, then, is called with mode="a".
        NOTE: at the date to code this function nor GCP, nor AWS support append_mode.

        if provide tqdm_kwargs, a progress bar will be displayed.

        :param path: the file to be writen
        :param data: the list of dicts to be saved to the file
        :param append_mode: flag to set append mode (default: False)
        :param tqdm_kwargs:
        :return: the number of objects written
        """
        # 1. compute the number of objects
        n_data = len(data)
        # 2. define the tqdm arguments if needed
        tqdm_write_kwargs = {
            **{
                "desc": f"jsonl_write('{path}')",
                "total": n_data
            },
            **tqdm_kwargs
        } if tqdm_kwargs is not None else tqdm_kwargs
        # 3. open the file if writing or append mode
        with smart_open.open(path, mode="w" if not append_mode else "a") as fp:
            # 3.1 define the iterator (tqdm(data) or data)
            data_iterator = tqdm(
                data, **
                tqdm_write_kwargs) if tqdm_write_kwargs is not None else data
            # 3.2  in writing mode new line prefix should be "", in append mode new line should be "\n"
            nl_prefix = "\n" if append_mode else ""
            # 3.3 iterate over all objects
            for obj in data_iterator:
                # parse object as a string
                line = nl_prefix + jsons.dumps(obj)
                # write a new line
                fp.write(line)
                # new line should be "\n"
                nl_prefix = "\n"

        # return the number of objects
        return n_data

    @classmethod
    def parallel_read(cls,
                      path: str,
                      mapping_class: Any = None,
                      offset: int = 0,
                      limit: int or None = None,
                      workers: int or None = None,
                      tqdm_kwargs: dict or None = None) -> list[dict]:
        """
        read a jsonl in parallel
        to optimize this process we divide it in two main steps:
        1. read the file line by line as a text (to not overload read process)
        2. parse content in parallel (parsing is the most expensive task)
        if workers is not defined will use the number of cpus in your computer
        :param path: the file to be read
        :param mapping_class: the output class (if defined)
        :param offset: read the file starting at this line (if defined)
        :param limit: read up to this number of lines
        :param workers: the number of parallel jobs
        :param tqdm_kwargs: if defined, this dictionary will be passed to tqdm when read the file
        :return: the list of documents parsed as dictionary or the mapping class
        """
        # define the number of workers to be used
        workers = workers if workers is not None else cpu_count()

        # 1. read the file in plain text
        with smart_open.open(path) as fp:
            # a. skip first `offset` lines
            _ = [_ for _, _ in zip(range(offset), fp)]
            # b. read up to `limit` lines
            limit_it = count() if limit is None else range(limit)
            zip_it = zip(limit_it, fp)

            reading_tqdm_kwargs = {
                **{
                    "total": limit,
                    "desc": "reading lines"
                },
                **tqdm_kwargs
            } if tqdm_kwargs is not None else None
            zip_it = tqdm(
                zip_it, **
                reading_tqdm_kwargs) if tqdm_kwargs is not None else zip_it

            lines = [line for _, line in zip_it]

        n = len(lines)

        # 2. parse each line in parallel
        # a. create the list of parameters
        parameters = [(line, mapping_class) for line in lines]
        with Pool(workers) as pool:
            # b. create a default tqdm kwargs
            tqdm_kwargs = {
                **{
                    "total": n,
                    "desc": f"parsing at {workers}x"
                },
                **tqdm_kwargs
            } if tqdm_kwargs is not None else None
            # c. if pass tqdm kwargs use the imap function in conjunction with tqdm
            #    or use the traditional map function without tqdm
            if tqdm_kwargs is not None:
                list_of_documents = list(
                    tqdm(pool.imap(_jsonl_parse_one_line, parameters),
                         **tqdm_kwargs))
            else:
                list_of_documents = pool.map(_jsonl_parse_one_line, parameters)

        # 3. return the list of documents
        return list_of_documents

    @classmethod
    def async_read(cls,
                   paths: list[str],
                   workers: int or None = None,
                   tqdm_kwargs: dict or None = None) -> list[dict]:
        """read a list of paths asynchronously"""
        # define the number of workers to be used
        workers = workers if workers is not None else cpu_count()

        # A.1. read all documents at once
        raw_contents = GsAsync.read(paths=paths, tqdm_kwargs=tqdm_kwargs)

        # A.2. define tqdm for split raw contents
        tqdm_kwargs_tmp = {
            **{
                "total": len(raw_contents),
                "desc": f"split contents at {workers}x"
            },
            **tqdm_kwargs
        } if tqdm_kwargs is not None else None

        with Pool(workers) as pool:
            if tqdm_kwargs_tmp is not None:
                list_of_lines = list(
                    tqdm(pool.imap(_split_str, raw_contents),
                         **tqdm_kwargs_tmp))
            else:
                list_of_lines = pool.map(_split_str, raw_contents)

        # A.3 define tqm for parse the contents
        tqdm_kwargs_tmp = {
            **{
                "total": len(list_of_lines),
                "desc": f"parsing documents at {workers}x"
            },
            **tqdm_kwargs
        } if tqdm_kwargs is not None else None

        with Pool(workers) as pool:
            if tqdm_kwargs_tmp is not None:
                list_of_documents = list(
                    tqdm(pool.imap(_parse_documents, list_of_lines),
                         **tqdm_kwargs_tmp))
            else:
                list_of_documents = pool.map(_parse_documents, list_of_lines)

        return list_of_documents

    @classmethod
    def parallel_write(cls,
                       path: str,
                       data: list[dict or object],
                       workers: int or None = None,
                       tqdm_kwargs: dict or None = None) -> int:
        """write in parallel"""
        workers = workers if workers is not None else cpu_count()
        data = data if isinstance(data, list) else [data]
        n = len(data)

        with Pool(workers) as pool:
            # b. create a default tqdm kwargs
            tqdm_kwargs = {
                **{
                    "total": n,
                    "desc": f"dumps at {workers}x"
                },
                **tqdm_kwargs
            } if tqdm_kwargs is not None else None
            # c. if pass tqdm kwargs use the imap function in conjunction with tqdm
            #    or use the traditional map function without tqdm
            if tqdm_kwargs is not None:
                lines = list(
                    tqdm(pool.imap(_jsonl_dumps_one_object, data),
                         **tqdm_kwargs))
            else:
                lines = pool.map(_jsonl_dumps_one_object, data)

            msg = f"writting content to '{path}'"
            logging.info(msg)
            content = "\n".join(lines)
            with smart_open.open(path, "w") as fp:
                fp.write(content)

            return len(content)
