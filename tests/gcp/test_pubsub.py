# Copyright (c) 2021-present Divinia, Inc.
"""PubSub testing"""
import os.path
from unittest.mock import patch, MagicMock

import jsons
import pandas as pd

from computing_toolbox.gcp.pubsub import PubSub, callback


class TestPubSub:
    """PubSub testing class"""

    def test_init(self):
        """test how to initialize a pubsub object"""
        queue = PubSub("my-project", "my-topic")
        assert queue

    @patch("computing_toolbox.gcp.pubsub.query.Query")
    def test_count(self, mock_query):
        """test hot to use the count method"""
        df0 = pd.DataFrame()
        df1 = pd.read_csv(os.path.join(os.path.dirname(__file__),
                                       "df-count-example.csv"),
                          header=[0, 1, 2],
                          index_col=0)

        # test for empty data
        mock_query.return_value.as_dataframe.return_value = df0
        queue = PubSub("my-project", "my-topic")
        n = queue.count()
        empty = queue.is_empty()
        assert n == 0
        assert empty

        # test for non-empty data
        mock_query.return_value.as_dataframe.return_value = df1
        queue = PubSub("my-project", "my-topic")
        n = queue.count()
        empty = queue.is_empty()
        assert n == 222  # this value is found in the mocked csv
        assert not empty

    @patch("computing_toolbox.gcp.pubsub.pubsub_v1.PublisherClient")
    def test_push(self, mock_client):
        """test how to push messages"""
        expected_message_id = 12345678
        mock_client.return_value.publish.return_value.result.return_value = expected_message_id

        data = {"name": "divinia"}
        queue = PubSub("my-project", "my-topic")
        flag = queue.push(data)
        assert flag

    @patch("computing_toolbox.gcp.pubsub.pubsub_v1.SubscriberClient")
    def test_pop(self, mock_client):
        """test how to pop messages"""
        expected_data = {"name": "divinia"}
        expected_b_message = jsons.dumps(expected_data).encode("utf-8")
        mock_message = MagicMock()
        mock_message.message.data = expected_b_message
        mock_client.return_value.pull.return_value.received_messages = [
            mock_message
        ]

        queue = PubSub("my-project", "my-topic")
        data = queue.pop()
        assert data == expected_data

        # test for empty messages
        mock_client.return_value.pull.return_value.received_messages = []
        data = queue.pop()
        assert not data

    def test_callback(self):
        """test the callback function"""
        future_obj = MagicMock()
        future_obj.result.return_value = "hello"

        response = callback(future=future_obj)
        assert response == "hello"

    @patch("computing_toolbox.gcp.pubsub.pubsub_v1.PublisherClient")
    @patch("computing_toolbox.gcp.pubsub.callback")
    @patch("computing_toolbox.gcp.pubsub.futures")
    def test_push_many(self, mock_futures, mock_callback, mock_client):
        """test how to push many messages in batches"""
        n = 13
        expected_id = "abc"
        expected_responses = [f"{expected_id}-{k}" for k in range(n)]

        mock_client.return_value.publish.return_value.result.return_value = expected_id
        mock_callback.return_value = "123"
        mock_futures.wait.return_value = expected_responses

        messages = [{"number": k} for k in range(n)]
        queue = PubSub("my-project", "my-topic")
        responses = queue.push_many(messages)
        assert all(responses)
