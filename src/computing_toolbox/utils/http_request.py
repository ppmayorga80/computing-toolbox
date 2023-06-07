"""http request is able to perform an http request with retries"""
import random
import time

import requests
from requests import Response
from tqdm import tqdm


class HttpRequest:
    """Http Request class able to execute a classical requests with retries and
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

        self.url: str = ""
        self.method: str = ""
        self.response: dict or None = None
        self.success: bool or None = None
        self.errors: list = []
        self.attempts: int = 0
        self.execution_time: float = -1

    def __str__(self):
        """string magic method to return the string representation of current object"""
        status_code = self.response.status_code if isinstance(
            self.response, Response) else "***"
        last_error = self.errors[-1] if self.errors else "---"
        emoji = ""
        message = ""

        if self.success is not None:
            if self.success:
                emoji = "🟢"
                message = f"status_code:{status_code}"
            else:
                emoji = "🔴"
                message = f"status_code:{status_code}, {last_error}"

        return f"HttpRequest: {emoji} | attempts:{self.attempts}/{self.max_attempts} | {self.url} | {message}"

    def request(self,
                method: str,
                url: str,
                params: dict or None = None,
                data: dict or None = None,
                headers: dict or None = None,
                timeout: float = 5,
                allow_redirects: bool = True,
                proxies: dict or None = None,
                tqdm_kwargs: dict or None = None,
                request_kwargs: dict or None = None) -> Response or None:
        """

        :param method: the request method
        :param url: the url to be requested
        :param params: a dictionary of parameters to be passed to the host (default: None)
        :param data: a dictionary of data to be passed to the host within the headers (default: None)
        :param headers: a dictionary with the headers to be used,
                you can find an example in your browser or generate a random one (default: None)
        :param timeout: How many seconds to wait for the server to send data before giving up.
                when timeout is reached, we try another attempt, when max_attempts is reached we return
                no Response (default: 5)
        :param allow_redirects: flag to use redirects (default: True)
        :param proxies: a dictionary of proxies to be used (default: None)
        :param tqdm_kwargs: if you want to see a tqdm progress bar, you can specify a not null value as a dictionary
                of parameters like: {} -> for default progress bar or {"desc":"Your Description"} -> for
                personal description, etc. (default: None)
        :param request_kwargs: extra arguments to be used in requests.request(**request_kwargs) method (default: None)
        :return: a request response or None if all attempts failed.
        """

        self.method = method
        self.url = url

        # set default kwargs for request
        request_kwargs = request_kwargs if request_kwargs is not None else {}
        default_request_kwargs = {
            **{
                "params": params,
                "data": data,
                "headers": headers,
                "timeout": timeout,
                "allow_redirects": allow_redirects,
                "proxies": proxies,
            },
            **request_kwargs
        }
        # filter not defined params
        default_request_kwargs = {
            k: v
            for k, v in default_request_kwargs.items() if v is not None
        }

        tqdm_default_kwargs = {
            "desc": f"HttpRequest.{self.method} Attempts:",
            "total": self.max_attempts
        }
        tqdm_default_kwargs = {
            **tqdm_default_kwargs,
            **tqdm_kwargs
        } if tqdm_kwargs is not None else tqdm_default_kwargs

        range_it = range(self.max_attempts)
        attempt_iterator = range_it if tqdm_kwargs is None else tqdm(
            range_it, **tqdm_default_kwargs)

        self.errors = []
        success = False
        response = None
        postfix_str = "⚪️"
        break_flag = False
        for k in attempt_iterator:
            if break_flag:
                break

            self.attempts = k + 1
            if tqdm_kwargs is not None:
                if len(self.errors) > 0:
                    postfix_str = f"🔴x{len(self.errors)}"
                    attempt_iterator.set_postfix_str(postfix_str)

            try:
                response = requests.request(method, url,
                                            **default_request_kwargs)
                if 200 <= response.status_code < 300:
                    success = True
                    break_flag = True
                    if tqdm_kwargs is not None:
                        postfix_str += "→🟢"
                        attempt_iterator.set_postfix_str(postfix_str)
                        attempt_iterator.update()

                # if not break <-> not success, then add an error
                self.errors.append(
                    ValueError(
                        f"failed request at attempt {k + 1} with status_code:{response.status_code}"
                    ))
            except Exception as error:
                self.errors.append(f"{error}")
                if self.rnd_sleep_interval:
                    a, b = self.rnd_sleep_interval
                    random_time = random.uniform(a, b)
                    time.sleep(random_time)

        if (tqdm_kwargs is not None) and success:
            attempt_iterator.set_postfix_str("🟢")

        self.success = success
        self.response = response
        return response
