"""The Elastic Search Long Search V2
get full index by processing in chunks and also
can write an output file every number of chunks (useful for big indexes)

this method is animated with a simple scroll bar
"""
import json
import logging
import os
from typing import Iterator

import smart_open
from elasticsearch import Elasticsearch
from tqdm import tqdm


class EsLongSearchGenerator:
    """ es_long_search_to_part_files computes/download the full index in batches of size `batch_size`
    and yield partial results after k processed batches and only compute a limited number of batches."""

    def __init__(self,
                 es: Elasticsearch,
                 index: str,
                 body: dict or None = None,
                 scroll: str = "1m",
                 batch_size: int = 100,
                 batch_limit: int or None = None,
                 tqdm_kwargs: dict or None = None):
        """ es_long_search_to_part_files computes/download the full index in batches of size `batch_size`
        and yield partial results after k processed batches and only compute a limited number of batches.

        For example:
        Consider you have 1M documents in your index and that every document weight 50KB,
        i.e. your entire index weights ~50GB.

        a. You can't use the traditional `es.search` because it crashes when you want to get more than 10K documents...
        b. You can't use the traditional es_long_search, because you will need to have more than 50GB of free memory...
        c. The solution is to use `es_long_search_generator` because we can use the `batch_size`=100 and
            yield partial documents after `yield_after_k_batches`=100 (i.e. every 100x100 processed documents).

        We encourage you to use the `body` parameter in order to select what fields you want to retrieve in order to make
        this process more lightweight in all aspects. For example:
            body={
                "_source":["name","city","zipcode"]
            }
        will get only 3 fields instead of the full document keys.

        :param es: open search client
        :param index: the index name
        :param body: search dictionary in json format
        :param batch_size: batch size, default=100
        :param scroll: time to hold search data to continued searches
        :param batch_limit: if defined, only process this number of batches
        :param tqdm_kwargs: tqdm extra arguments, if None tqdm is not displayed (default: None)
        """

        self.es = es
        self.index = index
        self.body = body
        self.scroll = scroll
        self.batch_size = batch_size
        self.batch_limit = batch_limit
        self.tqdm_kwargs = tqdm_kwargs

        self.total = 0
        self.total_chunks = 0
        self.last_k = 0
        self.last_scroll_id = ""

        self.last_scroll_id_path = os.path.join(
            os.environ["HOME"],
            f".EsLongSearchGenerator.last_scroll_id.{self.index}.json")

    def _store_last_scroll_id_path(self):
        """store last scroll id to a json file in order to use in the future with the resume function"""
        with smart_open.open(self.last_scroll_id_path, "w") as fp:
            data = {
                "total": self.total,
                "total_chunks": self.total_chunks,
                "last_k": self.last_k,
                "last_scroll_id": self.last_scroll_id
            }
            content = json.dumps(data)
            fp.write(content)

    def _load_last_scroll_id_path(self):
        """load the scroll id from a json file to use with the resume function"""
        with smart_open.open(self.last_scroll_id_path) as fp:
            content = fp.read()
        data = json.loads(content)
        self.last_k = data["last_k"]
        self.last_scroll_id = data["last_scroll_id"]
        self.total = data["total"]
        self.total_chunks = data["total_chunks"]

    def generate(self) -> Iterator[list]:
        """generate the iterator and return"""
        self.body = self.body if self.body is not None else {}
        input_tqdm_kwargs = self.tqdm_kwargs if self.tqdm_kwargs is not None else {}

        # 1. define the output variable
        # 2. create the first search
        try:
            response = self.es.search(index=self.index,
                                      body=self.body,
                                      size=self.batch_size,
                                      scroll=self.scroll)
        except Exception as error:
            msg = f"Error when execute EsLongSearchGenerator.generate: {error}"
            logging.error(msg)
            msg = f"Last ScrollID: '{self.last_scroll_id}'"
            logging.error(msg)
            self._store_last_scroll_id_path()
            return

        # 3. get the total number of documents and the number of chunks we have
        total = response["hits"]["total"]["value"] if response["hits"][
            "total"]["relation"] == "eq" else None
        total_chunks = (total // self.batch_size) + (total % self.batch_size
                                                     != 0) - 1
        self.total = total
        self.total_chunks = total_chunks

        # compute the tqdm parameters and define the chunk iterator
        input_tqdm_kwargs = {
            **{
                "total": total_chunks,
                "desc": f"es_long_search('{self.index}',body={self.body})"
            },
            **input_tqdm_kwargs
        }
        chunk_iterator = tqdm(
            range(1, 1 + total_chunks), **
            input_tqdm_kwargs) if self.tqdm_kwargs is not None else range(
                1, 1 + total_chunks)

        # 4. prepare the loop to get all the remaining responses
        scroll_id = response["_scroll_id"]
        self.last_scroll_id = scroll_id
        partial_documents = response['hits']['hits']

        # walk over the iterator
        for k in chunk_iterator:
            # yield partial documents
            self.last_k = k
            yield partial_documents
            partial_documents = []
            # test if we reach the limit
            if self.batch_limit and (k == self.batch_limit):
                break

            # 4.A get the new response providing the scroll_id value from the previous query
            try:
                response = self.es.scroll(scroll=self.scroll,
                                          scroll_id=scroll_id)
            except Exception as error:
                msg = f"Error when execute EsLongSearchGenerator.generate: {error}"
                logging.error(msg)
                msg = f"Last ScrollID: '{self.last_scroll_id}'"
                logging.error(msg)
                self._store_last_scroll_id_path()
                break

            # 4.B add new documents to the output variable
            partial_documents = response['hits']['hits']
            # 4.C update the scroll_id for the next query or loop
            scroll_id = response["_scroll_id"]
            self.last_scroll_id = scroll_id

        # 5. yield remaining documents if exists
        if partial_documents:
            yield partial_documents

        self._store_last_scroll_id_path()

    def resume(self) -> Iterator[list]:
        """resume function"""
        if not os.path.exists(self.last_scroll_id_path):
            msg = f"Can't resume, '{self.last_scroll_id_path}' doesn't exists"
            logging.warning(msg)
            return

        self._load_last_scroll_id_path()

        # compute the tqdm parameters and define the chunk iterator
        input_tqdm_kwargs = self.tqdm_kwargs if self.tqdm_kwargs is not None else {}
        input_tqdm_kwargs = {
            **{
                "total": self.total_chunks,
                "desc": f"es_long_search('{self.index}',body={self.body})"
            },
            **input_tqdm_kwargs
        }
        chunk_iterator = tqdm(
            range(self.last_k, 1 + self.total_chunks), **
            input_tqdm_kwargs) if self.tqdm_kwargs is not None else range(
                self.last_k, 1 + self.total_chunks)

        # 4. prepare the loop to get all the remaining responses

        # mimic last query
        scroll_id = self.last_scroll_id

        # walk over the iterator
        for j, _ in enumerate(chunk_iterator):
            # yield partial documents
            # test if we reach the limit
            if self.batch_limit and (j == self.batch_limit):
                break

            # 4.A get the new response providing the scroll_id value from the previous query
            try:
                response = self.es.scroll(scroll=self.scroll,
                                          scroll_id=scroll_id)
            except Exception as error:
                msg = f"Error when execute EsLongSearchGenerator.resume: {error}"
                logging.error(msg)
                msg = f"Last ScrollID: '{self.last_scroll_id}'"
                logging.error(msg)
                self._store_last_scroll_id_path()
                break

            # 4.B add new documents to the output variable
            partial_documents = response['hits']['hits']
            # 4.C update the scroll_id for the next query or loop
            scroll_id = response["_scroll_id"]
            self.last_scroll_id = scroll_id
            yield partial_documents

        self._store_last_scroll_id_path()
