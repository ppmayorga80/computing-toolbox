"""Test for elastic search long search"""
from unittest.mock import patch

from computing_toolbox.utils.es_long_search_generator import es_long_search_generator


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
        data = list(
            es_long_search_generator(es=es,
                                     index="my-index",
                                     body={},
                                     batch_size=self.batch_size,
                                     scroll="1m",
                                     yield_after_k_batches=1,
                                     batch_limit=None,
                                     tqdm_kwargs={}))
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
        for i, partial_data in enumerate(
                es_long_search_generator(es=es,
                                         index="my-index",
                                         body={},
                                         batch_size=self.batch_size,
                                         scroll="1m",
                                         yield_after_k_batches=1,
                                         batch_limit=1,
                                         tqdm_kwargs={})):
            assert partial_data == self.responses[i]['hits']['hits']
