"""cli command to perform elasticsearch long search

to connect to ElasticSearch, you must provide in order or precedence:
    environment variable ES_API_KEY or
    provide the optional argument --es-api-key
    if not provided am --es-host, connect to a local ES client

Usage:
    es_long_search [--verbose] [--es-host=HOST] [--es-api-key=APIKEY] <INDEX> <OUTPUT>

Arguments:
    <INDEX>     ElasticSearch index name
    <OUTPUT>    the output file to store information should be *.json or *.jsonl,
                optionally you can add .gz extension to compress the file

Options:
    --verbose               show verbose messages
    --es-api-key=APIKEY     the ElasticSearch ApiKey [default: ]
    --es-host=HOST          the ElasticSearch Host [default: localhost]

"""
import json
import os

import smart_open
from docopt import docopt
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

from computing_toolbox.utils.es_long_search import es_long_search
from computing_toolbox.utils.jsonl import Jsonl


def main_fn(es_host: str, es_api_key: str, index_name: str, output: str):
    """"main entry function
    to query all documents to an elasticsearch index and save them to an output file

    :param es_host: elasticsearch host
    :param es_api_key: elasticsearch api_key
    :param es_index_name: elasticsearch index name
    :param output: where to save the results
    """

    # 2. create the es client
    es_kwargs = {"api_key": es_api_key} if es_api_key else {}
    es = Elasticsearch(es_host, **es_kwargs)

    # 3. read the documents
    print("connecting with elasticsearch...")
    docs: list = es_long_search(es=es, index=index_name, tqdm_kwargs={})

    # 4. save the result if needed
    print(f"saving the output file '{output}'")
    if output.endswith(".jsonl") or output.endswith(".jsonl.gz"):
        Jsonl.write(path=output, data=docs, tqdm_kwargs={})
    else:
        with smart_open.open(output, "w") as fp:
            content = json.dumps(docs)
            fp.write(content)


def wrapper_main_fn():
    """wrapper main function"""
    load_dotenv()
    # 1. read arguments
    args = docopt(__doc__)
    # 2. parse arguments to variables
    es_host: str = args['--es-host']
    es_api_key_arg: str = args['--es-api-key']
    index: str = args['<INDEX>']
    output: str = args['<OUTPUT>']
    # compute the api key with a env variable or with the argument provided
    es_api_key_env = os.environ[
        'ES_API_KEY'] if 'ES_API_KEY' in os.environ else ''
    es_api_key = es_api_key_arg if es_api_key_arg else es_api_key_env

    # 3. call the main function
    main_fn(es_host=es_host,
            es_api_key=es_api_key,
            index_name=index,
            output=output)


if __name__ == '__main__':  # pragma: no cover
    wrapper_main_fn()
