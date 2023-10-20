"""The Elastic Search Long Search V2
get full index by processing in chunks and also
can write an output file every number of chunks (useful for big indexes)

this method is animated with a simple scroll bar
"""
from typing import Iterator

from elasticsearch import Elasticsearch
from tqdm import tqdm


def es_long_search_generator(
        es: Elasticsearch,
        index: str,
        body: dict or None = None,
        batch_size: int = 100,
        scroll: str = "1m",
        yield_after_k_batches: int = 100,
        batch_limit: int or None = None,
        tqdm_kwargs: dict or None = None) -> Iterator[list[str]]:
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
    :param yield_after_k_batches: yield partial results after k processed batches or loops.
    :param batch_limit: if defined, only process this number of batches
    :param tqdm_kwargs: tqdm extra arguments, if None tqdm is not displayed (default: None)
    :return: partial list of documents
    """

    input_body = body if body is not None else {}
    input_tqdm_kwargs = tqdm_kwargs if tqdm_kwargs is not None else {}

    # 1. define the output variable
    partial_documents = []
    # 2. create the first search
    response = es.search(index=index,
                         body=input_body,
                         size=batch_size,
                         scroll=scroll)
    # 3. get the total number of documents and the number of chunks we have
    total = response["hits"]["total"]["value"] if response["hits"]["total"][
        "relation"] == "eq" else None
    total_chunks = (total // batch_size) + (total % batch_size != 0) - 1

    # compute the tqdm parameters and define the chunk iterator
    input_tqdm_kwargs = {
        **{
            "total": total_chunks,
            "desc": f"es_long_search('{index}',body={body})"
        },
        **input_tqdm_kwargs
    }
    chunk_iterator = tqdm(
        range(1, 1 + total_chunks), **
        input_tqdm_kwargs) if tqdm_kwargs is not None else range(
            1, 1 + total_chunks)

    # 4. prepare the loop to get all the remaining responses
    scroll_id = response["_scroll_id"]
    partial_documents += response['hits']['hits']
    for k in chunk_iterator:
        if k % yield_after_k_batches == 0:
            # 4.1 if reach the number of loops, yield partial documents
            yield partial_documents
            partial_documents = []
        if batch_limit and (k == batch_limit):
            break

        # 4.A get the new response providing the scroll_id value from the previous query
        response = es.scroll(scroll=scroll, scroll_id=scroll_id)
        # 4.B add new documents to the output variable
        new_documents = response['hits']['hits']
        partial_documents += new_documents
        # 4.C update the scroll_id for the next query or loop
        scroll_id = response["_scroll_id"]

    # 5. yield remaining documents if exists
    if len(partial_documents) > 0:
        yield partial_documents
