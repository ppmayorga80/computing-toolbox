"""Test for elastic search long search"""
import os.path
from unittest.mock import patch

import pytest

from computing_toolbox.utils.es_long_search_to_part_files import es_long_search_to_part_files
from computing_toolbox.utils.jsonl import Jsonl


class TestEsLongSearchToPartFiles:
    """Test class for es_long_search method
    hits: contains 5 documents
    responses: contains 3 documents
        1st is the first response from es.search
        2nd is the first response from es.scroll
        3rd is the second response from es.scroll

    the es scroll function must be called with the _scroll_id
    value in order to continue the search operation in batches

    """
    hits = None
    responses = None
    initialized = False
    total = 11
    batch_size = 2

    def initialize(self):
        """Initialize the hits and responses"""
        if self.initialized:
            return

        self.hits = [{"_id": k, "name": f"n-{k}"} for k in range(self.total)]
        self.responses = [{
            "_scroll_id": "ABC-123",
            "hits": {
                "total": {
                    "value": self.total,
                    "relation": "eq"
                },
                "hits": self.hits[k:k + self.batch_size]
            }
        } for k in range(0, self.total, self.batch_size)]
        self.initialized = True

    @patch('elasticsearch.Elasticsearch')
    def test_es_long_search_to_part_files(self, mock_elastic_search,
                                          tmp_path_factory):
        """test es_long_search method by mocking elastic search methods"""
        # initialize the internal variables
        self.initialize()
        # instantiate the elastic search client (mocked)
        es = mock_elastic_search()
        # mimic the responses for es.search and es.scroll methods
        es.search.side_effect = self.responses[:1]
        es.scroll.side_effect = self.responses[1:]

        # test with path invalid format
        with pytest.raises(ValueError) as _:
            _ = es_long_search_to_part_files(
                es=es,
                index="my-index",
                batch_file_format=
                "/home/user/path/with/no/part/formatted/variable",
                save_after_k_batches=10,
                body={},
                batch_size=2)
        # test with invalid `save_after_k_batches`
        with pytest.raises(ValueError) as _:
            _ = es_long_search_to_part_files(
                es=es,
                index="my-index",
                batch_file_format="/home/user/path/file-part={part}.jsonl",
                save_after_k_batches=0,
                body={},
                batch_size=2)

        # because we set 5 documents and the size=2, the responses
        # will be split in 3 responses of sizes 1,2,2
        output_format = str(
            tmp_path_factory.mktemp("my-index") / "part-{part}.jsonl")
        paths = es_long_search_to_part_files(es=es,
                                             index="my-index",
                                             batch_file_format=output_format,
                                             save_after_k_batches=4,
                                             body={},
                                             batch_size=self.batch_size)

        # NOTE: not store all documents, you will probably get out of memory
        # this is only for testing purposes
        tmp_docs = []
        for path in paths:
            assert os.path.exists(path)
            data = Jsonl.read(path)
            tmp_docs += data

        assert tmp_docs == self.hits
