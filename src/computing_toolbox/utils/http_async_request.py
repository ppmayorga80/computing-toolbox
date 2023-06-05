"""asynchronuos request with same options as traditional requests library"""
import random
import time
from collections import Counter

import grequests
from requests import Response
from tqdm import tqdm

from computing_toolbox.utils.tictoc import tic, toc


class HttpAsyncRequest:
    """Http Async Request class able to execute a classical requests with retries and
    random sleep time between consecutive attempts"""

    def __init__(self,
                 max_attempts: int = 10,
                 rnd_sleep_interval: tuple[float, float] or None = None):
        """initialize http request
        in order to request an url, we will try at most `max_attempts` and sleeping
        a random amount of seconds between `rnd_sleep_interval[0]` and `rnd_sleep_interval[1]` if provided
        in order to be polite with the host.

        you can avoid `rnd_sleep_interval` in case you provide a rotating proxy when perform a request
        because sequential calls to the request method will be done with different proxy server.

        :param max_attempts: the max number of attempts to be done before exit and return nothing (default: 10)
        :param rnd_sleep_interval: 2-tuple to define a random value to wait between attempts,
        if no provided, no sleep is performed (default: None)
        """

        self.max_attempts: int = max_attempts
        self.rnd_sleep_interval: tuple[float, float] = rnd_sleep_interval

        self.urls: list[str] = []
        self.method: str = ""
        self.responses: list = []
        self.responses_history: list[list] = []
        self.success: list[bool] = []
        self.attempts: list[int] = []
        self.execution_time: float = -1

    def __str__(self):
        """string magic method to return the string representation of current object"""

        status_codes = [
            None if r is None else r.status_code for r in self.responses
        ]
        status_codes_counter = Counter(status_codes)
        status_codes_counter_list = [
            f"[{k}]x{v}" for k, v in status_codes_counter.items()
        ]
        status_codes_counter_str = ", ".join(status_codes_counter_list)

        total_attempts = sum(self.attempts)
        total_attempts_str = f"{total_attempts}" if total_attempts else "---"

        avg_attempts = sum(self.attempts) / len(
            self.attempts) if self.attempts else None
        avg_attempts_str = f"{avg_attempts:0.1f}" if avg_attempts else "---"

        n_success = sum(self.success)
        n_failures = len(self.success) - n_success
        n_success_str = f"🟢x{n_success}" if n_success else "-x-"
        n_failures_str = f"🔴x{n_failures}" if n_failures else "-x-"

        execution_time_str = f"{self.execution_time:0.3f} sec." if self.execution_time >= 0.0 else "---"
        return f"HttpAsyncRequest('{self.method}'): {n_success_str}, {n_failures_str} | status_codes:{status_codes_counter_str} | AVG(attempts):{avg_attempts_str} | TOTAL(attempts):{total_attempts_str} | Elapsed time: {execution_time_str}"

    def _fix_params(self,
                    urls: list[str],
                    params: list[dict] or None = None,
                    datas: list[dict] or None = None,
                    headers: list[dict] or None = None,
                    timeout: float or list[float] = 5,
                    allow_redirects: bool or list[bool] = True,
                    proxies: dict or None or list[dict] = None,
                    request_kwargs: dict or None = None,
                    tqdm_kwargs: dict or None = None):
        """fix parameters from `request` method, used only before `request` method is executed"""
        n_urls = len(urls)
        # fix null values -> list of None's
        params = params if params is not None else [None for _ in urls]
        datas = datas if datas is not None else [None for _ in urls]
        headers = headers if headers is not None else [None for _ in urls]

        timeout = [timeout for _ in range(n_urls)] if isinstance(
            timeout, (int, float)) else timeout
        allow_redirects = [allow_redirects
                           for _ in range(n_urls)] if isinstance(
                               allow_redirects, bool) else allow_redirects
        proxies = proxies if isinstance(
            proxies, list) else [proxies for _ in range(n_urls)]

        # set default kwargs for request
        request_kwargs = [request_kwargs for _ in urls
                          ] if request_kwargs is not None else [{}
                                                                for _ in urls]
        request_kwargs = [{
            **{
                "params": p,
                "data": d,
                "headers": h,
                "timeout": t,
                "allow_redirects": a,
                "proxies": x,
            },
            **r
        }
                          for r, p, d, h, t, a, x in zip(
                              request_kwargs, params, datas, headers, timeout,
                              allow_redirects, proxies)]
        # filter not defined params
        request_kwargs = [{
            k: v
            for k, v in r.items() if v is not None
        } for r in request_kwargs]

        # create a tqdm dictionary if necessary
        tqdm_kwargs = {
            **{
                "desc": f"HttpAsyncRequest.{self.method}x{n_urls}",
                "total": n_urls
            },
            **tqdm_kwargs
        } if tqdm_kwargs is not None else tqdm_kwargs

        # return parameters in the same order, now fixed
        return urls, params, datas, headers, timeout, allow_redirects, proxies, request_kwargs, tqdm_kwargs

    def request(self,
                method: str,
                urls: list[str],
                params: list[dict] or None = None,
                datas: list[dict] or None = None,
                headers: list[dict] or None = None,
                timeout: float = 5,
                allow_redirects: bool = True,
                proxies: dict or None = None,
                request_kwargs: dict or None = None,
                tqdm_kwargs: dict or None = None) -> Response or None:
        """

        :param method: the request method
        :param urls: the urls to be requested
        :param params: a list of all dictionaries of parameters to be passed to the host (default: None)
        :param datas: a list of all dictionaries of data to be passed to the host within the headers (default: None)
        :param headers: a list of dictionaries with the headers to be used,
                you can find an example in your browser or generate a random one (default: None)
        :param timeout: How many seconds to wait for the server to send data before giving up.
                when timeout is reached, we try another attempt, when max_attempts is reached we return
                no Response (default: 5)
        :param allow_redirects: flag to use redirects (default: True)
        :param proxies: a dictionary of proxies to be used (default: None)
        :param request_kwargs: extra arguments to be used in requests.request(**request_kwargs) method (default: None)
        :param tqdm_kwargs: if you want to see a tqdm progress bar, you can specify a not null value as a dictionary
                of parameters like: {} -> for default progress bar or {"desc":"Your Description"} -> for
                personal description, etc. (default: None)
        :return: a request response or None if all attempts failed.
        """
        tic(verbose=False)
        urls, params, datas, headers, timeout, allow_redirects, proxies, request_kwargs, tqdm_kwargs = self._fix_params(
            urls, params, datas, headers, timeout, allow_redirects, proxies,
            request_kwargs, tqdm_kwargs)

        self.method = method
        self.urls = urls
        n_urls = len(urls)

        range_it = range(n_urls)
        url_iterator = tqdm(
            range_it, **tqdm_kwargs) if tqdm_kwargs is not None else range_it
        attempt_iterator = range(self.max_attempts)

        attempts = [0 for _ in range(n_urls)]
        success = [False for _ in range(n_urls)]
        responses = [None for _ in range(n_urls)]
        responses_history = [[] for _ in range(n_urls)]

        pending_keys = [k for k in range(n_urls)]
        pending_urls = [url for url in urls]
        pending_request_kwargs = [kwargs for kwargs in request_kwargs]
        for attempt in attempt_iterator:
            request_stack = (
                grequests.request(method, url, **kwargs)
                for url, kwargs in zip(pending_urls, pending_request_kwargs))
            responses_stack = grequests.map(request_stack)

            tmp_pending_keys = []
            tmp_pending_urls = []
            tmp_pending_request_kwargs = []
            n_ok = 0
            for key, url, r_kwargs, response in zip(pending_keys, pending_urls,
                                                    pending_request_kwargs,
                                                    responses_stack):

                attempts[key] += 1
                responses[key] = response
                responses_history[key].append(response)

                if response is None or (response and
                                        not 200 <= response.status_code < 300):
                    tmp_pending_keys.append(key)
                    tmp_pending_urls.append(url)
                    tmp_pending_request_kwargs.append(r_kwargs)
                else:
                    n_ok += 1
                    success[key] = True

            pending_keys = tmp_pending_keys
            pending_urls = tmp_pending_urls
            pending_request_kwargs = tmp_pending_request_kwargs

            if isinstance(url_iterator, tqdm):
                url_iterator.set_postfix_str(
                    f"Attempt-Loop:{attempt + 1}, Attempts-Total:{sum(attempts)}, Pending:{len(pending_urls)}"
                )
                url_iterator.update(n_ok)

            if len(pending_keys) == 0:
                break

            if self.rnd_sleep_interval:
                a, b = self.rnd_sleep_interval
                random_time = random.uniform(a, b)
                time.sleep(random_time)

        self.responses = responses
        self.responses_history = responses_history
        self.success = success
        self.attempts = attempts

        self.execution_time = toc(verbose=False)
        return self.responses
