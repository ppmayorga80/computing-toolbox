"""generate fake or random http headers"""
from fake_headers import Headers


def generate_fake_headers(authority: str = "",
                          method: str = "get",
                          scheme: str = "https",
                          default_headers: dict or None = None) -> dict:
    """generate a fake headers to be used in requests

    :param authority: the authority or base site example: 'www.tripadvisor.com' (default: )
    :param method: the method to be used (default: get)
    :param scheme: the scheme or protocol to be used (default: https)
    :param default_headers: a default headers to take as a reference when the random/fake headers
            doesn't provide a key, (default: None)
    :return: a dictionary with a fake or random headers
    """
    # 1. define a default headers if necessary and make sure all keys are in lowercase
    # 1.1 regular headers from regular arguments
    regular_headers = {
        "authority": authority,
        "method": method,
        "scheme": scheme,
    }
    #1.2 default headers taken from a real browser or take the default_header from arguments
    default_headers = {
        "accept":
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-encoding":
        "gzip, deflate, br",
        "accept-language":
        "en-US,en;q=0.9,es;q=0.8",
        "cache-control":
        "max-age=0",
        "sec-fetch-dest":
        "document",
        "sec-fetch-mode":
        "navigate",
        "sec-fetch-site":
        "same-origin",
        "user-agent":
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36"
    } if default_headers is None else default_headers
    #1.3 merge regular headers and default headers
    default_headers = {**regular_headers, **default_headers}
    #1.4 make all keys lowercase
    default_headers = {k.lower(): v for k, v in default_headers.items()}

    # 2. define a fake-header object and generate a random headers
    header = Headers()
    fake_headers = header.generate()
    # 2.1 convert all keys in lower case to be compatible with default headers
    fake_headers = {k.lower(): v for k, v in fake_headers.items()}

    # 3. merge all headers
    merged_headers = {**default_headers, **fake_headers}

    # 4. filter empty values and return
    merged_headers = {k: v for k, v in merged_headers.items() if v}
    return merged_headers
