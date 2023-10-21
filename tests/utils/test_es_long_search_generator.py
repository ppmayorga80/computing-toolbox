"""Test for elastic search long search"""
import os
from unittest.mock import patch

from computing_toolbox.utils.es_long_search_generator import EsLongSearchGenerator


def my_side_effect():
    """raise an error on side effect"""
    raise ValueError("My Side Effect for ES")


class TestEsLongSearchGenerator:
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
    batch_size = 4

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
    def test_es_long_search_generator(self, mock_elastic_search):
        """test es_long_search method by mocking elastic search methods"""
        # initialize the internal variables
        self.initialize()
        # instantiate the elastic search client (mocked)
        es = mock_elastic_search()
        # mimic the responses for es.search and es.scroll methods
        es.search.side_effect = self.responses[:1]
        es.scroll.side_effect = self.responses[1:]

        # because we set 11 documents and the batch_size=4, the responses
        # will be split in 3 responses of sizes 4,4,3
        generator = EsLongSearchGenerator(es=es,
                                          index="my-index",
                                          body={},
                                          scroll="1m",
                                          batch_size=self.batch_size,
                                          batch_limit=None,
                                          tqdm_kwargs={})
        data = list(generator.generate())

        assert len(data) == self.total // self.batch_size + (
            self.total % self.batch_size != 0)
        assert sum(len(x) for x in data) == self.total

    @patch('elasticsearch.Elasticsearch')
    def test_es_long_search_generator_with_batch_limit(self,
                                                       mock_elastic_search):
        """test es_long_search method by mocking elastic search methods"""
        # initialize the internal variables
        self.initialize()
        # instantiate the elastic search client (mocked)
        es = mock_elastic_search()
        # mimic the responses for es.search and es.scroll methods
        es.search.side_effect = self.responses[:1]
        es.scroll.side_effect = self.responses[1:]

        # NOTE: not store all documents, you will probably get out of memory
        # this is only for testing purposes
        generator = EsLongSearchGenerator(es=es,
                                          index="my-index",
                                          body={},
                                          scroll="1m",
                                          batch_size=self.batch_size,
                                          batch_limit=1,
                                          tqdm_kwargs={})
        for i, partial_data in enumerate(generator.generate()):
            assert partial_data == self.responses[i]['hits']['hits']

    @patch('elasticsearch.Elasticsearch')
    def test_es_long_search_generator_with_resume(self, mock_elastic_search):
        """test es_long_search method by mocking elastic search methods"""
        # initialize the internal variables
        self.initialize()
        # instantiate the elastic search client (mocked)
        es = mock_elastic_search()
        # mimic the responses for es.search and es.scroll methods
        es.search.side_effect = self.responses[:1]
        es.scroll.side_effect = self.responses[1:]

        # NOTE: not store all documents, you will probably get out of memory
        # this is only for testing purposes
        generator = EsLongSearchGenerator(es=es,
                                          index="my-index",
                                          body={},
                                          scroll="1h",
                                          batch_size=self.batch_size,
                                          batch_limit=1,
                                          tqdm_kwargs={})
        last_i = 0
        for i, partial_data in enumerate(generator.generate()):
            assert partial_data == self.responses[i]['hits']['hits']
            last_i = i

        for j, partial_data in enumerate(generator.resume(), start=last_i + 1):
            assert partial_data == self.responses[j]['hits']['hits']

    @patch('elasticsearch.Elasticsearch')
    def test_es_long_search_generator_with_errors_example1(
            self, mock_elastic_search):
        """test es_long_search method by mocking elastic search methods"""
        # initialize the internal variables
        self.initialize()
        # instantiate the elastic search client (mocked)
        es = mock_elastic_search()
        # mimic the responses for es.search and es.scroll methods
        es.search.side_effect = my_side_effect
        es.scroll.side_effect = self.responses[1:]

        # NOTE: not store all documents, you will probably get out of memory
        # this is only for testing purposes
        generator = EsLongSearchGenerator(es=es,
                                          index="my-index",
                                          body={},
                                          scroll="1h",
                                          batch_size=self.batch_size,
                                          batch_limit=1,
                                          tqdm_kwargs={})
        for i, partial_data in enumerate(generator.generate()):
            assert partial_data == self.responses[i]['hits']['hits']

    @patch('elasticsearch.Elasticsearch')
    def test_es_long_search_generator_with_errors_example2(
            self, mock_elastic_search):
        """test es_long_search method by mocking elastic search methods"""
        # initialize the internal variables
        self.initialize()
        # instantiate the elastic search client (mocked)
        es = mock_elastic_search()
        # mimic the responses for es.search and es.scroll methods
        es.search.side_effect = self.responses[:1]
        es.scroll.side_effect = my_side_effect

        # NOTE: not store all documents, you will probably get out of memory
        # this is only for testing purposes
        generator = EsLongSearchGenerator(es=es,
                                          index="my-index",
                                          body={},
                                          scroll="1h",
                                          batch_size=self.batch_size,
                                          batch_limit=2,
                                          tqdm_kwargs={})
        i = 0
        for partial_data in generator.generate():
            assert partial_data == self.responses[i]['hits']['hits']
            i += 1

    @patch('elasticsearch.Elasticsearch')
    def test_es_long_search_generator_with_errors_example3(
            self, mock_elastic_search):
        """test es_long_search method by mocking elastic search methods"""
        # initialize the internal variables
        self.initialize()
        # instantiate the elastic search client (mocked)
        es = mock_elastic_search()
        # mimic the responses for es.search and es.scroll methods
        es.search.side_effect = self.responses[:2]
        es.scroll.side_effect = my_side_effect

        # NOTE: not store all documents, you will probably get out of memory
        # this is only for testing purposes
        generator = EsLongSearchGenerator(es=es,
                                          index="my-index",
                                          body={},
                                          scroll="1h",
                                          batch_size=self.batch_size,
                                          batch_limit=2,
                                          tqdm_kwargs={})
        last_i = -1
        for i, partial_data in enumerate(generator.generate()):
            last_i = i
            assert partial_data == self.responses[i]['hits']['hits']
        for j, partial_data in enumerate(generator.resume()):
            assert partial_data == self.responses[last_i + j +
                                                  1]['hits']['hits']

        os.unlink(generator.last_scroll_id_path)
        empty_data = list(generator.resume())
        assert not empty_data
