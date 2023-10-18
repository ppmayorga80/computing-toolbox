"""The Elastic Search Long Search V2
get full index by processing in chunks and also
can write an output file every number of chunks (useful for big indexes)

this method is animated with a simple scroll bar
"""
from elasticsearch import Elasticsearch
from tqdm import tqdm

from computing_toolbox.utils.jsonl import Jsonl


def es_long_search_to_part_files(
        es: Elasticsearch,
        index: str,
        batch_file_format: str,
        save_after_k_batches: int,
        body: dict or None = None,
        batch_size: int = 100,
        tqdm_kwargs: dict or None = None) -> list[str]:
    """ es_long_search_to_part_files computes/download the full index in batches of size `batch_size`
    and saves after k processed batch loops if `batch_file_format` is defined with {part} format variable.

    For example:
    Consider you have 1M documents in your index and that every document weight 50KB,
    i.e. your entire index weights ~50GB.

    a. You can't use the traditional `es.search` because it crashes when you want to get more than 10K documents...
    b. You can't use the traditional es_long_search, because you will need to have more than 50GB of free memory...
    c. The solution is to use `es_long_search_to_part_files` because we can use the `batch_size`=100 and
        write partial documents to a file after processing `save_after_k_batches`=50 (i.e. after 100x50 documents)
        and no return the list of batch files saved.

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
    :param batch_file_format: this is the full path where we write partial results in jsonl format,
                              if not provided, no partial files are saved.
                              ensure you use the following variable in the format `part`
                              examples:
                                    'gs://bucket/dir/to/write/partial-{part}.jsonl.gz'
                                    'gs://bucket/dir/to/write/partial-batch_counter={part}.jsonl'
                                    '/home/vader/path/to/death/star/file-batch_counter={part}.jsonl.gz'
    :param save_after_k_batches: if `temp_batch_file_format` is defined, saves partial results after k
                                        processed batches or loops.
    :param tqdm_kwargs: tqdm extra arguments, if None tqdm is not displayed (default: None)
    :return: the list of all saved files
    """
    # VERIFICATION STEP
    if "{part}" not in batch_file_format:
        raise ValueError(
            "`batch_file_format` must contain the {part} formatted variable")
    if save_after_k_batches < 1 or not isinstance(save_after_k_batches, int):
        raise ValueError(
            "`save_after_k_batches` must be an integer greater than zero")

    input_body = body if body is not None else {}
    input_tqdm_kwargs = tqdm_kwargs if tqdm_kwargs is not None else {}

    # 1. define the output variable
    partial_documents = []
    # 2. create the first search
    response = es.search(index=index,
                         body=input_body,
                         size=batch_size,
                         scroll="1m")
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
    all_paths = []
    part = 0
    for k in chunk_iterator:
        if k % save_after_k_batches == 0:
            # 4.1 if reach the number of loops, save the partial documents
            path = batch_file_format.format(part=part)
            part += 1
            all_paths.append(path)
            Jsonl.write(path=path,
                        data=partial_documents,
                        tqdm_kwargs={"desc": f"saving '{path}'"})
            partial_documents = []

        # 4.A get the new response providing the scroll_id value from the previous query
        response = es.scroll(scroll="1m", scroll_id=scroll_id)
        # 4.B add new documents to the output variable
        new_documents = response['hits']['hits']
        partial_documents += new_documents
        # 4.C update the scroll_id for the next query or loop
        scroll_id = response["_scroll_id"]

    # 5. save remaining documents if exists
    if len(partial_documents) > 0:
        path = batch_file_format.format(part=part)
        all_paths.append(path)
        Jsonl.write(path=path,
                    data=partial_documents,
                    tqdm_kwargs={"desc": f"saving '{path}'"})

    # 6. return all the saved paths
    return all_paths
