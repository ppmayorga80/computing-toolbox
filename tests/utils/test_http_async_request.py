"""test for http async request file"""
from unittest.mock import Mock

from aioresponses import aioresponses

from computing_toolbox.utils.http_async_request import HttpAsyncResponse, HttpAsyncRequest


def create_mock_client_response(status: int or None = 200):
    mock_response = Mock()
    mock_response.status = status
    return mock_response


class TestHttpAsyncResponse:
    """test for a http response class"""

    def test_set(self):
        """test set method"""
        response_ok = create_mock_client_response(200)
        response_fail = create_mock_client_response(404)
        value_error = ValueError("some error")

        response = HttpAsyncResponse()

        # test if set to success
        response.set(response_ok, "hello, world")
        assert response.success
        assert response.attempts == 1
        assert response.text == "hello, world"
        assert response.response_history[-1] is not None
        assert response.error_history[-1] is None

        # test for a failure
        response.set(response_fail, "")
        assert not response.success
        assert response.attempts == 2
        assert not response.text
        assert response.response_history[-1] is not None
        assert response.error_history[-1] is None

        # test for an error
        response.set_error(value_error)
        assert not response.success
        assert response.attempts == 3
        assert not response.text
        assert response.response_history[-1] is None
        assert response.error_history[-1] is not None


class TestHttpAsyncRequest:
    """class for testing http async request"""

    def test_init(self):
        """test the constructor"""
        requester = HttpAsyncRequest()
        assert requester.max_attempts > 0
        assert requester.rnd_sleep_interval is None
        assert not requester.urls
        assert not requester.method
        assert not requester.responses_history
        assert not requester.progress_bar

    def test_magic_str(self):
        """test the magic string method"""
        requester = HttpAsyncRequest()
        requester_str = str(requester)
        assert "HttpAsyncRequest" in requester_str

    def test_summary(self):
        """test summary function"""

        # 1. add some values to simulate results
        response_ok = create_mock_client_response(200)
        response_fail = create_mock_client_response(404)
        response_error = create_mock_client_response(None)
        value_error = ValueError("some error")

        resp1 = HttpAsyncResponse(flag="",
                                  response=response_ok,
                                  status_code=200,
                                  success=True,
                                  text="hello, world",
                                  attempts=1,
                                  response_history=[response_ok],
                                  error_history=[None])
        resp2 = HttpAsyncResponse(
            flag="",
            response=response_fail,
            status_code=404,
            success=False,
            text="",
            attempts=2,
            response_history=[response_fail, response_fail],
            error_history=[None, None])
        resp3 = HttpAsyncResponse(
            flag="",
            response=response_error,
            status_code=None,
            success=False,
            text="",
            attempts=2,
            response_history=[response_fail, response_error],
            error_history=[None, value_error])

        # 2. create the requester
        requester = HttpAsyncRequest()

        requester.method = "GET"
        requester.urls = ["a", "b", "c"]
        requester.responses_history = [resp1, resp2, resp3]

        summary1 = requester.summary()
        summary2 = requester.summary(exclude_success=True,
                                     exclude_failures=True,
                                     exclude_errors=True)
        assert len(summary1) == 3
        assert not summary2

        assert sum(1 for x in summary1
                   if x["status_code"] and x["status_code"] == 200) == 1
        assert sum(1 for x in summary1
                   if x["status_code"] and x["status_code"] == 404) == 1
        assert sum(1 for x in summary1 if x["status_code"] is None) == 1

    def test_request_v1(self):
        """test the request with default values"""

        urls = ["/url/1", "/url/2", "/url/3"]

        # B. define an example with retries
        with aioresponses() as m:
            # B.1 define the results for the urls (two times to match the number of retries)
            m.get(urls[0], payload="hello, world from page 1")
            m.get(urls[1], payload="hello, world from page 2")
            m.get(urls[2], payload="hello, world from page 3")

            requester = HttpAsyncRequest()
            requester.request("GET", urls)
            assert isinstance(requester.responses_history, list)
            assert len(requester.responses_history) == 3
            assert sum(1 for r in requester.responses_history
                       if r.status_code == 200) == 3

    def test_request_v1_with_tqdm(self):
        """test the request with default values"""

        urls = ["/url/1", "/url/2", "/url/3"]

        # B. define an example with retries
        with aioresponses() as m:
            # B.1 define the results for the urls (two times to match the number of retries)
            m.get(urls[0], payload="hello, world from page 1")
            m.get(urls[1], status=404)
            m.get(urls[1], status=404)
            m.get(urls[2], status=404)  # second will be an error

            requester = HttpAsyncRequest(max_attempts=2)
            requester.request("GET", urls, tqdm_kwargs={})

            assert isinstance(requester.responses_history, list)
            assert len(requester.responses_history) == 3
            assert sum(1 for r in requester.responses_history
                       if r.status_code == 200) == 1
            assert sum(1 for r in requester.responses_history
                       if r.status_code == 404) == 1
            assert sum(1 for r in requester.responses_history
                       if r.status_code is None) == 1

    def test_request_with_list_parameters(self):
        """test with predefined values"""

        urls = ["/url/1", "/url/2", "/url/3"]

        # B. define an example with retries
        with aioresponses() as m:
            # B.1 define the results for the urls (two times to match the number of retries)
            m.get(urls[0], payload="hello, world from page 1")
            m.get(urls[1], payload="hello, world from page 1")
            m.get(urls[2], payload="hello, world from page 1")

            requester = HttpAsyncRequest(max_attempts=2)
            requester.request("GET", urls, timeout=[3, 4, 5], tqdm_kwargs={})

            assert isinstance(requester.responses_history, list)

    def test_request_with_random_sleep_interval(self):
        """test with predefined values"""

        urls = ["/url/1", "/url/2", "/url/3"]

        # B. define an example with retries
        with aioresponses() as m:
            # B.1 define the results for the urls (two times to match the number of retries)
            m.get(urls[0], status=404)
            m.get(urls[0], payload="hello, world from page 1")
            m.get(urls[1], payload="hello, world from page 1")
            m.get(urls[2], payload="hello, world from page 1")

            requester = HttpAsyncRequest(max_attempts=2,
                                         rnd_sleep_interval=(0.001, 0.002))
            requester.request("GET", urls, timeout=[3, 4, 5], tqdm_kwargs={})

            assert isinstance(requester.responses_history, list)
