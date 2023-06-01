"""Test http request"""
import re
from unittest.mock import patch, Mock

from computing_toolbox.utils.http_request import HttpRequest


def create_mock_response(status_code: int = 200):
    mock_response = Mock()
    mock_response.status_code = status_code
    return mock_response


class TestHttpRequest:
    """Class for testing HttpRequest class"""

    def test_init(self):
        """test constructor and default values"""
        requester = HttpRequest(max_attempts=1, rnd_sleep_interval=(1, 3))
        assert requester.max_attempts == 1
        assert requester.rnd_sleep_interval == (1, 3)
        assert requester.url == ""
        assert requester.method == ""
        assert requester.response is None

    def test_str(self):
        """test for a string conversion"""
        requester = HttpRequest(max_attempts=1, rnd_sleep_interval=(1, 3))
        text = str(requester)
        assert re.findall(r"^HttpRequest:\s+\|\s+attempts:.*$", text)

        # if we have success=True
        for flag in (False, True):
            requester.success = flag  # set this flag just for testing purposes
            text = f"{requester}"
            assert re.findall(
                r"^HttpRequest:.*\s+\|\s+attempts:.*\|.*\|\s+status_code:.*$",
                text)

    @patch("computing_toolbox.utils.http_request.requests")
    def test_request_without_tqdm(self, mock_requests):
        """testing the request method"""
        # A.1 configure the mocking to have success at first time
        mock_requests.request.side_effect = [
            create_mock_response(status_code=200)
        ]

        # A.2 execute the request
        requester = HttpRequest(max_attempts=3)
        response = requester.request("GET", "http://www.hello-world.com")
        assert response.status_code == 200
        assert requester.success
        assert requester.attempts == 1

        # B.1 configure the mocking to have success at attempt number 5
        mock_requests.request.side_effect = [
            ConnectionError("Some connection error"),
            ConnectionError("Some connection error"),
            create_mock_response(status_code=200)
        ]

        # B.2 execute the request
        requester = HttpRequest(max_attempts=3)
        response = requester.request("GET", "http://www.hello-world.com")
        assert response.status_code == 200
        assert requester.success
        assert requester.attempts == 3

        # C.1 configure the mocking to have no success with sleeping intervals
        mock_requests.request.side_effect = [
            create_mock_response(status_code=404),
        ]
        # C.2 execute the request
        requester = HttpRequest(max_attempts=3,
                                rnd_sleep_interval=(0.00001, 0.00002))
        response = requester.request("GET", "http://www.hello-world.com")
        assert response.status_code == 404
        assert not requester.success
        assert requester.attempts == 3

    @patch("computing_toolbox.utils.http_request.requests")
    def test_request_with_tqdm(self, mock_requests):
        """repeat the same testing as the previous method but with tqdm configuration"""
        # A.1 configure the mocking to have success at first time
        mock_requests.request.side_effect = [
            create_mock_response(status_code=200)
        ]

        # A.2 execute the request
        requester = HttpRequest(max_attempts=3)
        response = requester.request("GET",
                                     "http://www.hello-world.com",
                                     tqdm_kwargs={})
        assert response.status_code == 200
        assert requester.success
        assert requester.attempts == 1

        # B.1 configure the mocking to have success at attempt number 5
        mock_requests.request.side_effect = [
            ConnectionError("Some connection error"),
            ConnectionError("Some connection error"),
            create_mock_response(status_code=200)
        ]

        # B.2 execute the request
        requester = HttpRequest(max_attempts=3)
        response = requester.request("GET",
                                     "http://www.hello-world.com",
                                     tqdm_kwargs={})
        assert response.status_code == 200
        assert requester.success
        assert requester.attempts == 3

        # C.1 configure the mocking to have no success with sleeping intervals
        mock_requests.request.side_effect = [
            create_mock_response(status_code=404),
        ]
        # C.2 execute the request
        requester = HttpRequest(max_attempts=3,
                                rnd_sleep_interval=(0.00001, 0.00002))
        response = requester.request("GET",
                                     "http://www.hello-world.com",
                                     tqdm_kwargs={})
        assert response.status_code == 404
        assert not requester.success
        assert requester.attempts == 3
