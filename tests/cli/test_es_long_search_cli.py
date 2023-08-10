"""testing es_long_search client app"""
import json
import os
import sys
from unittest.mock import patch

import smart_open

from computing_toolbox.cli.es_long_search_cli import wrapper_main_fn
from computing_toolbox.utils.jsonl import Jsonl


@patch('computing_toolbox.cli.es_long_search_cli.Elasticsearch')
@patch('computing_toolbox.cli.es_long_search_cli.es_long_search')
def test_wrapper_main_fn(mock_es_long_search, mock_elasticsearch, tmp_path):
    """testing how to call wrapper_main_fn with 2 options:
    the output as a jsonl and the output as json
    """

    # mock values
    expected_data = [{"name": "foo"}, {"name": "bar"}]
    mock_es_long_search.return_value = expected_data
    mock_elasticsearch.return_value = None

    # inject apikey env variable
    os.environ["ES_API_KEY"] = "put a real api key here"

    # test1: with jsonl extension
    # inject system arguments for docopt
    output = str(tmp_path / "output.jsonl")
    sys.argv = ["", "my-index-name", output]

    # call the function
    wrapper_main_fn()

    # verify the file exists and is what we expected
    assert os.path.exists(output)
    data = Jsonl.read(output)
    assert data == expected_data
    # ==============================

    # test2: with json extension
    output = str(tmp_path / "output.json")
    sys.argv = ["", "my-index-name", output]

    # call the function
    wrapper_main_fn()

    # verify the file exists and is what we expected
    assert os.path.exists(output)
    with smart_open.open(output, "r") as fp:
        data = json.loads(fp.read())
    assert data == expected_data
