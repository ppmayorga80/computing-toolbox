"""asynchronous request with same options as traditional requests library"""
from collections import Counter

from tqdm import tqdm


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

        self.progress_bar: tqdm or None = None

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

    @classmethod
    def expand_to_list(cls, data, n):
        """expand data to a list if needed"""
        if isinstance(data, list):
            return data
        return [data for _ in range(n)]

    def fix_params(self,
                   urls: list[str],
                   params: list[dict] or dict or None = None,
                   headers: list[dict] or dict or None = None,
                   timeout: float or list[float] = 5,
                   allow_redirects: bool or list[bool] = True,
                   proxies: dict or list[dict] or None = None,
                   request_kwargs: dict or None = None,
                   tqdm_kwargs: dict or None = None):
        """fix parameters from `request` method, used only before `request` method is executed"""
        n_urls = len(urls)
        # fix null values -> list
        params = self.expand_to_list(params, n_urls)
        headers = self.expand_to_list(headers, n_urls)
        timeout = self.expand_to_list(timeout, n_urls)
        allow_redirects = self.expand_to_list(allow_redirects, n_urls)
        proxies = self.expand_to_list(proxies, n_urls)

        # set default kwargs for request
        request_kwargs = request_kwargs if request_kwargs is not None else {}
        request_kwargs = self.expand_to_list(request_kwargs, n_urls)
        request_kwargs = [
            {
                **{
                    "params": p,
                    "headers": h,
                    "timeout": t,
                    "allow_redirects": a,
                    "proxies": x,
                },
                **r
            }
            for r, p, h, t, a, x in zip(
                request_kwargs, params, headers, timeout,
                allow_redirects, proxies
            )
        ]
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
        return urls, params, headers, timeout, allow_redirects, proxies, request_kwargs, tqdm_kwargs


if __name__ == '__main__':
    requester = HttpAsyncRequest(10)
    a = requester.fix_params(["a", "b"])
    for ak in a:
        print(ak)
