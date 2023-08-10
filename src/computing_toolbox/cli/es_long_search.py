"""cli command to perform elasticsearch long search

to connect to ElasticSearch, you must provide in order or precedence:
    environment variable ES_API_KEY or
    provide the optional argument --es-api-key
    if not provided, connect to a local ES client

Usage:
    es_long_search [--verbose] [--es-host=HOST] [--es-api-key=APIKEY] <INDEX> <OUTPUT>

Arguments:
    <INDEX>     ElasticSearch index name
    <OUTPUT>    the output file to store information should be *.json or *.jsonl,
                optionally you can add .gz extension to compress the file

Options:
    --verbose               show verbose messages
    --es-api-key=APIKEY     the ElasticSearch ApiKey
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

if __name__ == '__main__':
    load_dotenv()

    # 1. read arguments
    args = docopt(__doc__)

    es_host: str = args['--es-host']
    es_api_key_arg: str = args['--es-api-key']
    index: str = args['<INDEX>']
    output: str = args['<OUTPUT>']
    # compute the api key with a env variable or with the argument provided
    es_api_key_sys = os.environ['ES_API_KEY'] if 'ES_API_KEY' in os.environ else ''
    es_api_key = es_api_key_arg if es_api_key_arg else es_api_key_sys

    # 2. create the es client
    es_kwargs = {"api_key": es_api_key} if es_api_key else {}
    es = Elasticsearch(es_host, **es_kwargs)

    # 3. read the documents
    print("connecting with elasticsearch...")
    docs: list = es_long_search(es=es, index=index, tqdm_kwargs={})

    # 4. save the result if needed
    print(f"saving the output file '{output}'")
    if output.endswith(".jsonl") or output.endswith(".jsonl.gz"):
        Jsonl.write(path=output, data=docs, tqdm_kwargs={})
    else:
        with smart_open.open(output, "w") as fp:
            content = json.dumps(docs)
            fp.write(content)
