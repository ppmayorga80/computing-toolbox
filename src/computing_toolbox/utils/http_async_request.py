"""asynchronous request with same options as traditional requests library"""
import asyncio
import base64
import random
from collections import Counter
from dataclasses import dataclass, field

import aiohttp
from aiohttp.client_reqrep import ClientResponse
from tqdm import tqdm

from computing_toolbox.utils.deep_get import deep_get
from computing_toolbox.utils.tictoc import tic, toc

HTTP_SUCCESS_SYMBOL = "🟢"  # for status_code==[2**]
HTTP_FAILURE_SYMBOL = "⭕️"  # for status_code!=[2**]
HTTP_ERROR_SYMBOL = "🔴"  # for exceptions or errors


@dataclass
class HttpAsyncResponse:
    """Custom class for the http response (aiohttp has status variable not status_code)"""
    flag: str = ""
    response: ClientResponse or None = None
    status_code: int or None = None
    success: bool = False
    text: str = ""
    attempts: int = 0
    response_history: list[ClientResponse
                           or None] = field(default_factory=list)
    error_history: list[Exception or None] = field(default_factory=list)

    def set(self, response: ClientResponse, text: str):
        """properly set variables for a given response,
         detect success or failure and update other variables as needed"""
        self.response = response
        self.status_code = response.status
        self.success = 200 <= response.status < 300
        self.flag = HTTP_SUCCESS_SYMBOL if self.success else HTTP_FAILURE_SYMBOL
        self.text = text
        self.attempts += 1
        self.response_history.append(response)
        self.error_history.append(None)

    def set_error(self, error):
        """properly set variables for a given error"""
        self.response = None
        self.status_code = None
        self.success = False
        self.flag = HTTP_ERROR_SYMBOL
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
        self.responses_history: list[HttpAsyncResponse] = []
        self.execution_time: float = -1

        self.progress_bar_increment: float = 1.0
        self.progress_bar: tqdm or None = None

    def __str__(self):
        """string magic method to return the string representation of current object"""
        n_urls = len(self.urls)

        # 1. count and group status codes
        status_codes = (r.status_code for r in self.responses_history
                        if r.status_code)
        status_codes_counter = Counter(status_codes)
        status_codes_counter_list = [
            f"[{k}]x{v}" for k, v in status_codes_counter.items()
        ]
        status_codes_counter_str = ", ".join(status_codes_counter_list)

        # 2. compute total attempts
        attempts = [r.attempts for r in self.responses_history]
        total_attempts = sum(attempts)
        total_attempts_str = f"{total_attempts}" if total_attempts else "---"
        # 2.1 and the average attempts
        avg_attempts = total_attempts / len(attempts) if attempts else None
        avg_attempts_str = f"{avg_attempts:0.1f}" if avg_attempts else "---"

        # 3. compute number of success and failures -> errors by difference
        success = [1 for r in self.responses_history if r.success]
        failures = [
            1 for r in self.responses_history
            if r.status_code and not 200 <= r.status_code < 300
        ]
        n_success = sum(success)
        n_failures = sum(failures)
        n_errors = n_urls - n_success - n_failures
        n_success_str = f"{HTTP_SUCCESS_SYMBOL}x{n_success}" if n_success else "-x-"
        n_failures_str = f"{HTTP_FAILURE_SYMBOL}x{n_failures}" if n_failures else "-x-"
        n_error_str = f"{HTTP_ERROR_SYMBOL}x{n_errors}" if n_errors else "-x-"

        # 4. count and group error codes
        error_codes = (type(r.error_history[-1]).__name__
                       for r in self.responses_history
                       if r.error_history and r.error_history[-1])
        error_codes_counter = Counter(error_codes)
        error_codes_counter_list = [
            f"[{k}]x{v}" for k, v in error_codes_counter.items()
        ]
        error_codes_counter_str = ", ".join(error_codes_counter_list)

        # 5. compute execution time
        execution_time_str = f"{self.execution_time:0.3f} sec." if self.execution_time >= 0.0 else "---"

        # group output in a list to display in different lines
        lines = [
            f"{n_success_str}, {n_failures_str}, {n_error_str}",
            f"status_codes:{status_codes_counter_str}",
            f"error_codes:{error_codes_counter_str}",
            f"AVG(attempts):{avg_attempts_str}",
            f"TOTAL(attempts):{total_attempts_str}",
            f"Elapsed time: {execution_time_str}"
        ]
        lines_str = "\n\t ".join(lines)

        # return the string representation of this object
        string_representation = f"HttpAsyncRequest.{self.method}x{n_urls}: {lines_str}"
        return string_representation

    def summary(self,
                exclude_success: bool = False,
                exclude_failures: bool = False,
                exclude_errors: bool = False) -> list[dict]:
        """computes a summary of the request

        :param exclude_success: if true, exclude the success urls (default: False)
        :param exclude_failures: if true, exclude the failures urls (default: False)
        :param exclude_errors: if true, exclude the errors urls (default: False)
        :return: the list of urls with summary information
        """
        # 1. create empty lists
        success_list = []
        failure_list = []
        error_list = []

        # 2. compute success list
        if not exclude_success:
            url_success_pairs = [
                (k, url, r.status_code, r.attempts) for k, url, r in zip(
                    range(len(self.urls)), self.urls, self.responses_history)
                if r.success
            ]
            success_list = [{
                "url_index": k,
                "url": url,
                "status_code": status_code,
                "attempts": attempts,
                "max_attempts": self.max_attempts,
                "error": None
            } for k, url, status_code, attempts in url_success_pairs]

        # 3. compute failure list
        #    if exists status_code and not success
        if not exclude_failures:
            url_failure_pairs = [
                (k, url, r.status_code, r.attempts) for k, url, r in zip(
                    range(len(self.urls)), self.urls, self.responses_history)
                if r.status_code and not 200 <= r.status_code < 300
            ]
            failure_list = [{
                "url_index": k,
                "url": url,
                "status_code": status_code,
                "attempts": attempts,
                "max_attempts": self.max_attempts,
                "error": None
            } for k, url, status_code, attempts in url_failure_pairs]

        # 4. compute error list
        #   has error_list and the last attempt was an error
        if not exclude_errors:
            url_error_pairs = [
                (k, url, r.status_code, r.attempts, r.error_history[-1])
                for k, url, r in zip(range(len(self.urls)), self.urls,
                                     self.responses_history)
                if r.error_history and r.error_history[-1]
            ]
            error_list = [{
                "url_index": k,
                "url": url,
                "status_code": status_code,
                "attempts": attempts,
                "max_attempts": self.max_attempts,
                "error": {
                    "name": type(e).__name__,
                    "class": str(e.__class__),
                    "message": str(e)
                }
            } for k, url, status_code, attempts, e in url_error_pairs]

        # concatenate the list and sort as the same order as self.urls
        summary_list = success_list + failure_list + error_list
        summary_list = sorted(summary_list, key=lambda x: x["url_index"])
        return summary_list

    def _update_progress_bar(self, success, attempts):
        """updates self.progress_bar given the current number of success and attempts
        this function should be called within request_one method i.e. by one async method at a time
        """
        # A. if we not have a progress bar, return
        if not self.progress_bar:
            return

        # B. update progress bar

        # B.1 update increments (for failures or errors, the increment is in decimals)
        if success:
            # move the remaining increment
            remaining_increment = 1.0 - (attempts -
                                         1) * self.progress_bar_increment
            self.progress_bar.update(remaining_increment)
        else:
            # move a little forward
            self.progress_bar.update(self.progress_bar_increment)

        # B.2 update postfix string
        # B.2.1 attempts
        attempts = [r.attempts for r in self.responses_history]
        total_attempts = sum(attempts)
        total_attempts_str = f"{total_attempts}" if total_attempts else "---"

        # B.2.1 success, failures and errors
        success = len([1 for r in self.responses_history if r.success])
        failures = sum(1 for r in self.responses_history
                       if r.status_code and not 200 <= r.status_code < 300)
        errors = sum(1 for r in self.responses_history
                     if r.error_history and r.error_history[-1])

        # B.3 compute a summary list to build a string
        summary_list = []
        summary_list += [f"{HTTP_SUCCESS_SYMBOL}x{success}"] if success else []
        summary_list += [f"{HTTP_FAILURE_SYMBOL}x{failures}"
                         ] if failures else []
        summary_list += [f"{HTTP_ERROR_SYMBOL}x{errors}"] if errors else []
        summary_str = ", ".join(summary_list)

        # B.4 update the progress bar postfix string
        postfix_str = f"Total-Attempts:{total_attempts_str}, {summary_str}"
        self.progress_bar.set_postfix_str(postfix_str)

    @classmethod
    def _expand_to_list(cls, data, n):
        """expand data to a list if needed, useful because with this class
        we can provide single object as a parameter, and we need to fix them
        converting those values in a list of the same length as the input urls"""
        if isinstance(data, list):
            return data
        return [data for _ in range(n)]

    def _fix_params(self,
                    urls: list[str],
                    params: list[dict] or dict or None = None,
                    jsons: list[dict] or dict or None = None,
                    headers: list[dict] or dict or None = None,
                    timeout: float or list[float] = 5,
                    allow_redirects: bool or list[bool] = True,
                    proxies: dict or list[dict] or None = None,
                    request_kwargs: dict or None = None,
                    tqdm_kwargs: dict or None = None):
        """fix parameters from `request` method, used only before `request` method is executed"""
        n_urls = len(urls)

        # fix null values -> list
        params = self._expand_to_list(params, n_urls)
        jsons = self._expand_to_list(jsons, n_urls)
        headers = self._expand_to_list(headers, n_urls)
        timeout = self._expand_to_list(timeout, n_urls)
        allow_redirects = self._expand_to_list(allow_redirects, n_urls)
        proxies = self._expand_to_list(proxies, n_urls)

        # fix proxies for aiohttp (because this class use a string proxy representation)
        proxies = [
            deep_get(p, ["https"], deep_get(p, ["http"], None)) if isinstance(
                p, dict) else p for p in proxies
        ]

        # set default kwargs for request
        request_kwargs = request_kwargs if request_kwargs is not None else {}
        request_kwargs = self._expand_to_list(request_kwargs, n_urls)
        request_kwargs = [{
            **{
                "params": p,
                "json": j,
                "headers": h,
                "timeout": t,
                "allow_redirects": a,
                "proxy": x,
            },
            **r
        }
                          for r, p, j, h, t, a, x in zip(
                              request_kwargs, params, jsons, headers, timeout,
                              allow_redirects, proxies)]
        # filter not defined params
        request_kwargs = [{
            k: v
            for k, v in r.items() if v is not None
        } for r in request_kwargs]

        # create a tqdm dictionary if necessary
        self.progress_bar_increment = 1.0 / self.max_attempts
        tqdm_kwargs = {
            **{
                "desc":
                f"HttpAsyncRequest.{self.method}x{n_urls}",
                "total":
                len(urls),
                "bar_format":
                "{l_bar}{bar}| {n:0.1f}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]"
            },
            **tqdm_kwargs
        } if tqdm_kwargs is not None else tqdm_kwargs

        # return parameters in the same order, now fixed
        return urls, request_kwargs, tqdm_kwargs

    async def _request_one(
            self,
            session: aiohttp.ClientSession,
            method: str,
            url: str,
            request_kwargs: dict,
            attempt_countdown: int,
            last_response: HttpAsyncResponse,
            progress_bar: tqdm or None = None) -> HttpAsyncResponse:
        """request one single url and perform a retry-loop if needed using recursivity

        :param session: the session object of the aiohttp
        :param method: the method to be used
        :param url: the url to be requested
        :param request_kwargs: additional args to be passed to the aiohttp-request method
        :param attempt_countdown: current attempt iteration,
                must be set as self.max_attempts prior to call this function.
        :param last_response: a response object passed through this function and store
                the last response
        :param progress_bar: if provided, is a tqdm progress bar to be updated
        :return: the last response object
        """
        # decide if we can continue or not (recursivity)
        if attempt_countdown == 0:
            return last_response
        if attempt_countdown != self.max_attempts and self.rnd_sleep_interval:
            a, b = self.rnd_sleep_interval
            rand_dt = random.uniform(a, b)
            await asyncio.sleep(rand_dt)

        # 1. compute the request step
        try:
            async with session.request(method, url,
                                       **request_kwargs) as response:
                # retrieve the html text and the final url
                text = await response.text()

                # update the last response based on the status code and update progress bar
                last_response.set(response, text)
                self._update_progress_bar(last_response.success,
                                          last_response.attempts)

                # if failure, call this function again (recursion)
                if not last_response.success:
                    result = await self._request_one(
                        session=session,
                        method=method,
                        url=url,
                        request_kwargs=request_kwargs,
                        attempt_countdown=attempt_countdown - 1,
                        last_response=last_response,
                        progress_bar=progress_bar)

                    return result

                return last_response

        except Exception as error:
            # in case of an exception, report it
            last_response.set_error(error)
            self._update_progress_bar(last_response.success,
                                      last_response.attempts)

            # 5. in case of an error, retry with the same parameters (recursion)
            result = await self._request_one(
                session=session,
                method=method,
                url=url,
                request_kwargs=request_kwargs,
                attempt_countdown=attempt_countdown - 1,
                last_response=last_response,
                progress_bar=progress_bar)
            return result

    async def _request_many(
            self, method: str, urls: list[str], request_kwargs: list[dict],
            tqdm_kwargs: dict or None) -> list[HttpAsyncResponse]:
        """request many urls (call many times request_one method
        urls and request_kwargs must be of the same size

        :param method: the method to be used
        :param urls: the list of urls to be requested
        :param request_kwargs: the list of additional arguments for individual request
        :param tqdm_kwargs: the parameters for a tqdm progress bar
        :return: the list of responses of the same size and in the same order as urls.
        """
        # A. create the client session
        async with aiohttp.ClientSession() as session:
            # A.1 create the list of responses and progress bar
            self.responses_history = [HttpAsyncResponse() for _ in urls]

            # A.2create the progress bar if needed
            range_it = range(len(urls))
            self.progress_bar = tqdm(range_it, **
                                     tqdm_kwargs) if tqdm_kwargs else None

            # A.3 construct the list of tasks to be requested
            tasks = [
                asyncio.ensure_future(
                    self._request_one(session=session,
                                      method=method,
                                      url=url_k,
                                      request_kwargs=request_kwargs_k,
                                      attempt_countdown=self.max_attempts,
                                      last_response=response_k,
                                      progress_bar=self.progress_bar))
                for url_k, request_kwargs_k, response_k in zip(
                    urls, request_kwargs, self.responses_history)
            ]
            # A.4 execute all tasks asynchronously
            results = await asyncio.gather(*tasks)

            # A.5 return results
            return results

    def request(self,
                method: str,
                urls: list[str],
                batch_size: int = 50,
                params: list[dict] or dict or None = None,
                jsons: list[dict] or dict or None = None,
                headers: list[dict] or dict or None = None,
                timeout: float or list[float] = 5,
                allow_redirects: bool or list[bool] = True,
                proxies: dict or list[dict] or None = None,
                request_kwargs: dict or None = None,
                tqdm_kwargs: dict or None = None) -> list[HttpAsyncResponse]:
        """Entry point, this method calls the async code defined above
        to request many urls, all with the same method and personalized params, headers, etc.
        all arguments should be defined as a single value and, we convert them to a list
        representation.

        If you want a progress bar, set tqdm_kwargs as a dictionary,
        {} for a default configuration

        :param method: the http method GET,POST,...
        :param urls: the list of urls
        :param batch_size: we can process a large number of urls in batches to make it optimum
        :param params: additional parameters to be used in the GET request (default: None)
        :param jsons: additional parameters to be used in the POST request (default: None)
        :param headers: the headers to be used in the request (default: None)
        :param timeout: timeout for individual request (default: 5)
        :param allow_redirects: flag to allow redirects (default: True)
        :param proxies: proxy dictionary (default: None(
        :param request_kwargs: additional arguments to be used in the request (default: None)
        :param tqdm_kwargs: parameters for a tqdm progress bar, use {} for default configuration (default: None)
        :return: the list of responses
        """

        # start the measure of the execution time
        key = base64.b64encode(str(__file__).encode("ascii")).decode("ascii")
        tic(key=key, verbose=False)

        # save method and urls to the current object, remaining object variables
        # are updated at run time
        self.method = method
        self.urls = urls

        tqdm_kwargs = {
            **tqdm_kwargs,
            **{
                "position": 1,
                "leave": False
            }
        } if tqdm_kwargs is not None else None
        results = []
        for k in tqdm(range(0, len(urls), batch_size),
                      desc=f"async-request, batch_size:{batch_size}",
                      position=0,
                      leave=True):
            subset_urls = urls[k:k + batch_size]

            # fix all input parameters as a list if needed, after this step
            # all information is stored in `request_kwargs`
            subset_urls, request_kwargs, tqdm_kwargs = self._fix_params(
                subset_urls, params, jsons, headers, timeout, allow_redirects,
                proxies, request_kwargs, tqdm_kwargs)

            # call the request async method `request_many`
            subset_results = asyncio.run(
                self._request_many(method, subset_urls, request_kwargs,
                                   tqdm_kwargs))
            results += subset_results

        # compute the execution time by difference
        self.execution_time = toc(key=key, verbose=False)

        # return the results
        return results
