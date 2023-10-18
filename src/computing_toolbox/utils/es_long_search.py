"""ElasticSearch Long Search
ES search function can only return up to 10000 documents
if we want more than 10K docs, we need to get the _scroll_id
from a 1st call of the search method and then use the
scroll method with the _scroll_id in order to get remaining documents
(just like to process in chunks)
In this method we precompute the total number of documents and then
figure out how many times we need to call the scroll method to finally
return the full list of documents.

this method is animated with a simple scroll bar

"""
from elasticsearch import Elasticsearch
from tqdm import tqdm


def es_long_search(es: Elasticsearch,
                   index: str,
                   body: dict or None = None,
                   size: int = 100,
                   tqdm_kwargs: dict or None = None) -> list[dict]:
    """Perform elastic-search (ES) search in chunks in order to get more than 10K documents
    which is the maximum value for ES search method.

    We encourage you to use the `body` parameter in order to select what fields you want to retrieve in order to make
    this process more lightweight in all aspects. For example:
        body={
            "_source":["name","city","zipcode"]
        }
    will get only 3 fields instead of the full document keys.        

    :param es: open search client
    :param index: the index name
    :param body: search dictionary in json format
    :param size: chunk size, default=100
    :param tqdm_kwargs: tqdm extra arguments, if None tqdm is not displayed (default: None)
    :return: the list of all documents
    """
    input_body = body if body is not None else {}
    input_tqdm_kwargs = tqdm_kwargs if tqdm_kwargs is not None else {}

    # 1. define the output variable
    all_documents = []
    # 2. create the first search
    response = es.search(index=index, body=input_body, size=size, scroll="1m")
    # 3. get the total number of documents and the number of chunks we have
    total = response["hits"]["total"]["value"] if response["hits"]["total"][
        "relation"] == "eq" else None
    total_chunks = (total // size) + (total % size != 0) - 1

    # compute the tqdm parameters and define the chunk iterator
    input_tqdm_kwargs = {
        **{
            "total": total_chunks,
            "desc": f"es_long_search('{index}',body={body})"
        },
        **input_tqdm_kwargs
    }
    chunk_iterator = tqdm(
        range(total_chunks), **
        input_tqdm_kwargs) if tqdm_kwargs is not None else range(total_chunks)

    # 4. prepare the loop to get all the remaining responses
    scroll_id = response["_scroll_id"]
    all_documents += response['hits']['hits']
    for _ in chunk_iterator:
        # 4.A get the new response providing the scroll_id value from the previous query
        response = es.scroll(scroll="1m", scroll_id=scroll_id)
        # 4.B add new documents to the output variable
        new_documents = response['hits']['hits']
        all_documents += new_documents
        # 4.C update the scroll_id for the next query or loop
        scroll_id = response["_scroll_id"]

    # 5. get all the documents
    return all_documents
