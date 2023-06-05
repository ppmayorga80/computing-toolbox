"""test for http async request file"""
import re
from unittest.mock import patch, Mock

from computing_toolbox.utils.http_async_request import HttpAsyncRequest


def create_mock_response(status_code: int = 200):
    mock_response = Mock()
    mock_response.status_code = status_code
    return mock_response


class TestHttpAsyncRequest:
    """test class for HttpAsyncRequest"""
    MOCK_200_RESPONSE = create_mock_response(200)
    MOCK_201_RESPONSE = create_mock_response(201)
    MOCK_202_RESPONSE = create_mock_response(202)
    MOCK_404_RESPONSE = create_mock_response(404)
    MOCK_NONE_RESPONSE = None

    def test_init_str_fix_params(self):
        """test 3 methods"""
        # 1. test constructor
        requester = HttpAsyncRequest()
        assert requester.max_attempts == 10
        assert requester.rnd_sleep_interval is None
        assert not requester.urls
        assert not requester.method
        assert not requester.responses
        assert not requester.responses_history
        assert not requester.success
        assert not requester.attempts
        assert requester.execution_time < 0

        # 2, test magic method __str__
        text = str(requester)
        assert re.findall(
            r"HttpAsyncRequest\(\'[^()]*\'\).*status_codes:.*AVG\(attempts\):.*TOTAL\(attempts\):.*Elapsed time:.*",
            text)

        # 3. test _fix_params method
        #    even we use all defaults (None values)
        #    we get fixed values
        input_urls = ["/my/page/1", "/my/page/2"]
        urls, params, datas, headers, timeout, allow_redirects, proxies, request_kwargs, tqdm_kwargs = requester._fix_params(
            input_urls)
        assert urls == input_urls
        assert isinstance(params, list) and len(params) == len(urls)
        assert isinstance(datas, list) and len(datas) == len(urls)
        assert isinstance(headers, list) and len(headers) == len(urls)
        assert isinstance(timeout, list) and len(timeout) == len(urls)
        assert isinstance(allow_redirects,
                          list) and len(allow_redirects) == len(urls)
        assert isinstance(proxies, list) and len(proxies) == len(urls)
        assert isinstance(request_kwargs,
                          list) and len(request_kwargs) == len(urls)
        assert tqdm_kwargs is None  # not default tqdm_kwargs

    @patch("computing_toolbox.utils.http_async_request.grequests")
    def test_request_no_retries(self, mock_grequests):
        """test the async http request with no retries i.e.
        all requests are completed at first attempt
        """
        # 1. define the urls to test
        my_urls = ["/page/1", "other/page", "my/third/page"]

        # 2. set mocking values
        mock_success_response = create_mock_response(200)
        mock_grequests.request.return_value = None
        mock_grequests.map.return_value = [
            mock_success_response for _ in range(len(my_urls))
        ]

        # execute the async request and test
        requester = HttpAsyncRequest()
        responses = requester.request("GET", my_urls)
        assert len(responses) == len(my_urls)
        assert all(r.status_code == 200 for r in responses)

    @patch("computing_toolbox.utils.http_async_request.grequests")
    def test_request_with_bad_responses(self, mock_grequests):
        """test async http request with 4 attempts out of 5.
        the 4th attempt complete the request with all success
        """
        # 1. define the urls to test
        my_urls = [
            "http://www.mypage.com/1", "http://www.mypage.com/2",
            "http://www.mypage.com/3"
        ]

        # 2. set mocking values
        mock_grequests.request.return_value = "not matter"
        # setting responses:
        # 1st attempt: [200,404,404] #out first url
        # 2nd attempt: [None,202] # out third url
        # 3th attempt: [404]
        # 4th attempt: [200]
        expected_response_list = [[
            self.MOCK_200_RESPONSE, self.MOCK_404_RESPONSE,
            self.MOCK_404_RESPONSE
        ], [self.MOCK_NONE_RESPONSE, self.MOCK_202_RESPONSE],
                                  [self.MOCK_404_RESPONSE],
                                  [self.MOCK_201_RESPONSE]]
        mock_grequests.map.side_effect = expected_response_list

        # execute the async request and test
        requester = HttpAsyncRequest(max_attempts=5,
                                     rnd_sleep_interval=(0.001, 0.002))
        responses = requester.request("GET", my_urls, tqdm_kwargs={})
        assert len(responses) == len(my_urls)
        assert responses[0].status_code == 200
        assert responses[1].status_code == 201
        assert responses[2].status_code == 202
        assert sum(requester.attempts) == sum(
            len(x) for x in expected_response_list)

    @patch("computing_toolbox.utils.http_async_request.grequests")
    def test_request_with_one_failed(self, mock_grequests):
        """test async request with one failed
        configure the mock request in order to
        success with 1st and 3rd url but the second one
        fails up to the end.
        """
        # 1. define the urls to test
        my_urls = [
            "http://www.other.com/1", "http://www.other.com/2",
            "http://www.other.com/3"
        ]

        # 2. set mocking values
        mock_grequests.request.return_value = None
        # setting responses:
        # 1st attempt: [200,404,404] #out first url
        # 2nd attempt: [404,202] # out third url
        # 3th attempt: [404]
        # 4th attempt: [404]
        # 5th attempt: [404] #this make 2nd url isn't success
        expected_response_list = [[
            self.MOCK_200_RESPONSE, self.MOCK_404_RESPONSE,
            self.MOCK_404_RESPONSE
        ], [self.MOCK_404_RESPONSE, self.MOCK_202_RESPONSE],
                                  [self.MOCK_404_RESPONSE],
                                  [self.MOCK_404_RESPONSE],
                                  [self.MOCK_404_RESPONSE]]
        mock_grequests.map.side_effect = expected_response_list

        # execute the async request and test
        requester = HttpAsyncRequest(max_attempts=5,
                                     rnd_sleep_interval=(0.001, 0.002))
        responses = requester.request("GET", my_urls, tqdm_kwargs={})
        assert len(responses) == len(my_urls)
        assert responses[0].status_code == 200
        assert responses[1].status_code == 404
        assert responses[2].status_code == 202
        assert sum(requester.attempts) == sum(
            len(x) for x in expected_response_list)
