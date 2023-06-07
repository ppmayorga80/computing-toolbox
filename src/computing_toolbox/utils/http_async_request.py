"""asynchronous request with same options as traditional requests library"""
import asyncio
from collections import Counter
from dataclasses import dataclass, field

import aiohttp
from aiohttp.client_reqrep import ClientResponse
from tqdm import tqdm


@dataclass
class HttpAsyncResponse:
    response: ClientResponse or None = None
    status_code: int = -1
    success: bool = False
    text: str = ""
    attempts: int = 0
    response_history: list[ClientResponse or None] = field(default_factory=list)
    error_history: list[Exception or None] = field(default_factory=list)

    def set(self, response, text):
        self.response = response
        self.status_code = response.status
        self.success = (200 <= response.status < 300)
        self.text = text
        self.attempts += 1
        self.response_history.append(response)
        self.error_history.append(None)

    def set_error(self, error):
        self.response = None
        self.status_code = -1
        self.success = False
        self.text = ""
        self.attempts += 1
        self.response_history.append(None)
        self.error_history.append(error)


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
        self.statuses: list = []
        self.texts: list = []
        self.responses_history: list[list] = []
        self.error_history: list[list] = []
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
        return urls, request_kwargs, tqdm_kwargs

    async def request_one_url(self,
                              session: aiohttp.ClientSession,
                              method,
                              url,
                              request_kwargs,
                              attempt_countdown: int,
                              last_response: HttpAsyncResponse,
                              progress_bar: tqdm or None = None
                              ):
        # decide if we can continue or not
        if attempt_countdown == 0:
            return last_response

        # 1. compute the request step
        try:
            async with session.request(
                    method,
                    url,
                    **request_kwargs) as response:
                # retrieve the html text and the final url
                text = await response.text()
                last_response.set(response, text)

                if not last_response.success:
                    result = await self.request_one_url(
                        session=session,
                        method=method,
                        url=url,
                        request_kwargs=request_kwargs,
                        attempt_countdown=attempt_countdown - 1,
                        last_response=last_response,
                        progress_bar=progress_bar
                    )
                    return result

                return last_response

        except Exception as e:
            # in case of an exception, report it
            last_response.set_error(e)

            # 5. in case of an error, retry with the same parameters
            result = await self.request_one_url(
                session=session,
                method=method,
                url=url,
                request_kwargs=request_kwargs,
                attempt_countdown=attempt_countdown - 1,
                last_response=last_response,
                progress_bar=progress_bar
            )
            return result


async def main():
    my_urls = [
        'http://python-requests.org',
        'http://httpbin.org',
        'http://python-guide.org',
        'http://kennethreitz.com'
    ]
    requester = HttpAsyncRequest(10)
    urls, request_kwargs, tqdm_kwargs = requester.fix_params(
        my_urls)

    async with aiohttp.ClientSession() as session:
        the_response = HttpAsyncResponse()
        x = await requester.request_one_url(session, "GET", urls[2], request_kwargs[0], attempt_countdown=10,
                                            last_response=the_response)
        print(x)


if __name__ == '__main__':
    asyncio.run(main())
#https://www.twilio.com/blog/asynchronous-http-requests-in-python-with-aiohttp