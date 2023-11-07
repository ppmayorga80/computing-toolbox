"""testing the deep_key file"""

from computing_toolbox.utils.deep_key import deep_key


def test_deep_key():
    """test deep_key function"""
    x = {
        "person": [{
            "name": "foo",
            "age": 10
        }, {
            "name": "bar",
            "age": 20
        }],
        "age": [30, 40]
    }
    a = list(deep_key(x, "age"))
    assert a == [[30, 40], 10, 20]
