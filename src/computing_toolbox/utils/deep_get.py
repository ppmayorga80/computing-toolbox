"""This script provides a function able to search for a series of keys/index
    over a given object and return the value or a default in case a key doesn't
    exist or is None.

    For example:
    x={"name":{"first":"John","last":"Lennon"},"age":[None]}
    deep_get(x,["name","last"],"") -> "Lennon"
    deep_get(x,["name","last","middle"],"") -> ""
    deep_get(x,["age",0],3) -> 3

"""

from typing import Union


def deep_get(obj: Union[dict, list], path: list[Union[str, int]],
             default_value: any):
    """Gets the value at `path` of `x`.
    If the resolved value is None or some value in path doesn't exist,
    the `default_value` is returned in its place.

    :param obj: Object to search
    :param path: list of keys/int for successive deep search
    :param default_value: default value in case a key doesn't exist or the value is None
    :return: the value of the key list or default value in case of error
    """

    tmp_obj = obj
    for k in path:
        if tmp_obj is None:
            return default_value
        if isinstance(tmp_obj, dict):
            if k in tmp_obj:
                tmp_obj = tmp_obj[k]
            else:
                return default_value
        elif isinstance(tmp_obj, list) and isinstance(k, int):
            if 0 <= k < len(tmp_obj):
                tmp_obj = tmp_obj[k]
            else:
                return default_value
        else:
            return default_value

    if tmp_obj is None:
        return default_value

    return tmp_obj
