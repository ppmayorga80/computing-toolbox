"""deep key is a function able to find a key deeply
 in the object and return a list of values for that particular key"""
from typing import Iterator, Any


def deep_key(node: Any, key: Any) -> Iterator:
    """find all sub-objects with the key
    example:
        x = {"person":[{"name":"foo", "age":10},{"name":"bar", "age":20}],"age":[30,40]}
        a = list(deep_key(x,"age"))
    result:
        a = [[30, 40], 10, 20]
    explanation:
        the first result is [30,40] because the algorithm searches in deep order

    :param node: the input object
    :param key: the key to find
    :return: the list of sub-objects with key=`key`
    """
    if isinstance(node, list):
        # 1. if a list, search the key for every element in the node
        for i in node:
            for x in deep_key(i, key):
                # 1.1 if find it, yield it
                yield x
    elif isinstance(node, dict):
        # 2. if a dict, yield it if the key is present in the node
        if key in node:
            yield node[key]
        # 3. additionally, search on all the possible values of the node
        for j in node.values():
            for x in deep_key(j, key):
                # 3.1 if find it, yield it
                yield x
