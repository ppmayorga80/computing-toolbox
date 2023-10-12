"""generate fake or random http headers"""
from fake_headers import Headers

DEFAULT_HEADERS = {
    'accept':
    'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language':
    'en',
    'sec-ch-ua':
    '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
    'sec-ch-ua-mobile':
    '?0',
    'sec-ch-ua-platform':
    '"macOS"',
    'sec-fetch-dest':
    'document',
    'sec-fetch-mode':
    'navigate',
    'sec-fetch-site':
    'none',
    'sec-fetch-user':
    '?1',
    'upgrade-insecure-requests':
    '1',
    'user-agent':
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}


def generate_fake_headers(authority: str = "",
                          method: str = "get",
                          scheme: str = "https",
                          base_headers: dict or None = None) -> dict:
    """generate a fake headers to be used in requests

    :param authority: the authority or base site example: 'www.tripadvisor.com' (default: )
    :param method: the method to be used (default: get)
    :param scheme: the scheme or protocol to be used (default: https)
    :param base_headers: the headers to fill it out with the random/fake headers (default: None)
    :return: a dictionary with a fake or random headers
    """
    # 1. define a default headers if necessary and make sure all keys are in lowercase
    # 1.1 regular headers from regular arguments
    regular_headers = {
        "authority": authority,
        "method": method,
        "scheme": scheme,
    }
    regular_headers = {k.lower(): v for k, v in regular_headers.items() if v}

    # 1.2 default headers taken from a real browser or take the default_header from arguments
    base_headers = base_headers if base_headers else {}
    # 1.3 make all keys lowercase and clean empty values
    base_headers = {k.lower(): v for k, v in base_headers.items() if v}

    # 2. define a fake-header object and generate a random headers
    header = Headers()
    fake_headers = header.generate()
    # 2.1 convert all keys in lower case to be compatible with default headers
    fake_headers = {k.lower(): v for k, v in fake_headers.items() if v}

    # 3. merge all headers by precedence
    merged_headers = {
        **DEFAULT_HEADERS,
        **fake_headers,
        **regular_headers,
        **base_headers
    }

    # 4. filter empty values and return
    merged_headers = {k: v for k, v in merged_headers.items() if v}
    return merged_headers
