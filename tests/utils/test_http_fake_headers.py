"""Testing http fake/random headers for requests"""
from computing_toolbox.utils.http_fake_headers import generate_fake_headers


def test_generate_fake_headers():
    """function to test different ways to generate fake headers"""

    # 1. fake headers without authority, default_headers
    header = generate_fake_headers()
    assert isinstance(header, dict)
    assert "authority" not in header
    assert "method" in header
    assert all(v for _, v in header.items())  # test have all values

    # 2. with authority but default_headers
    header = generate_fake_headers(authority="www.google.com")
    assert isinstance(header, dict)
    assert "authority" in header
    assert "method" in header
    assert all(v for _, v in header.items())
    assert all(k.islower() for k in header)

    # 3. with authority and default_headers
    header = generate_fake_headers(authority="www.google.com",
                                   default_headers={"name": "foo"})
    assert isinstance(header, dict)
    assert "authority" in header
    assert ("name" in header) and (header["name"] == "foo")
    assert all(v for _, v in header.items())
    assert all(k.islower() for k in header)
