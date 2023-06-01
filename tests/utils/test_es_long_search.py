"""Test for elastic search long search"""
from unittest.mock import patch

from computing_toolbox.utils.es_long_search import es_long_search


class TestEsLongSearch:
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

    def initialize(self):
        """Initialize the hits and responses"""
        if self.initialized:
            return

        self.hits = [{"_id": k, "name": f"n-{k}"} for k in range(5)]
        self.responses = [{
            "_scroll_id": "ABC-123",
            "hits": {
                "total": {
                    "value": 5,
                    "relation": "eq"
                },
                "hits": self.hits[:1]
            }
        }, {
            "_scroll_id": "ABC-456",
            "hits": {
                "total": {
                    "value": 5,
                    "relation": "eq"
                },
                "hits": self.hits[1:3]
            }
        }, {
            "_scroll_id": "ABC-789",
            "hits": {
                "total": {
                    "value": 5,
                    "relation": "eq"
                },
                "hits": self.hits[3:5]
            }
        }]
        self.initialized = True

    @patch('elasticsearch.Elasticsearch')
    def test_es_long_search(self, mock_elastic_search):
        """test es_long_search method by mocking elastic search methods"""
        # initialize the internal variables
        self.initialize()
        # instantiate the elastic search client (mocked)
        es = mock_elastic_search()
        # mimic the responses for es.search and es.scroll methods
        es.search.side_effect = self.responses[:1]
        es.scroll.side_effect = self.responses[1:]

        # because we set 5 documents and the size=2, the responses
        # will be split in 3 responses of sizes 1,2,2
        docs = es_long_search(es, "my-index", body={}, size=2)
        assert docs
        assert docs == self.hits
