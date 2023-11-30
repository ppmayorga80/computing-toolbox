# Copyright (c) 2021-present Divinia, Inc.
"""Handle PubSub messages"""
import datetime
import logging

from concurrent import futures

import jsons
from google.api_core import retry
from google.cloud import monitoring_v3
from google.cloud.monitoring_v3 import query
from google.cloud import pubsub_v1
from tqdm import tqdm


def callback(future: pubsub_v1.publisher.futures.Future) -> str:
    message_id = future.result()
    return message_id


class PubSub:
    """PubSub (Queue) with basic operations
    1. push -> insert
    2. pop -> get and delete
    3. front -> get
    4. empty -> True if empty
    5. count -> Number of messages
    """

    DEFAULT_SUBSCRIPTION_ID_FORMAT = "{topic_id}-sub"

    def __init__(self,
                 project_id: str,
                 topic_id: str,
                 subscription_id: str = ""):
        """Instantiate a queue by name or Enum value
        :param topic_id: queue name str
        :project_id: project id
        :subscription_id: the subscription id, if empty, build a default one [default:]
        """
        self.project_id: str = project_id
        self.topic_id: str = topic_id
        self.subscription_id = subscription_id if subscription_id else self.DEFAULT_SUBSCRIPTION_ID_FORMAT.format(
            topic_id=self.topic_id)

    def count(self) -> int:
        """Total number of messages this value is approximate until GCP updates the query
        is not real time!!!
        you will need to wait 2min in order to get right values
        see: https://cloud.google.com/monitoring/api/metrics_gcp#gcp-pubsub
        """

        client = monitoring_v3.MetricServiceClient()
        result = query.Query(
            client,
            self.project_id,
            'pubsub.googleapis.com/subscription/num_undelivered_messages',
            end_time=datetime.datetime.now(),
            minutes=2,
        ).as_dataframe()
        n = 0
        if result.shape[0] > 0:
            n = result["pubsub_subscription"][self.project_id][
                self.subscription_id].max()
        return n

    def is_empty(self) -> bool:
        """True if empty"""
        n = self.count()
        return n == 0

    def push(self, body: dict) -> bool:
        """📥 Push or Insert a message to the SQS"""
        publisher = pubsub_v1.PublisherClient()

        topic_path = publisher.topic_path(self.project_id, self.topic_id)
        body_str = jsons.dumps(body)
        data = body_str.encode("utf-8")
        # When you publish a message, the client returns a future.
        future = publisher.publish(topic_path, data=data)

        message_id = future.result()
        return message_id != 0

    def push_many(self,
                  documents: list[dict],
                  batch_size: int = 100,
                  tqdm_kwargs: dict or None = None) -> list[bool]:
        """Push many messages in a pubsub"""
        batch_settings = pubsub_v1.types.BatchSettings(
            max_messages=batch_size,  # default 100
            max_bytes=1 * 1024 * 1024,  # default 1 MB
            max_latency=1.0,  # default 10 ms
        )
        publisher = pubsub_v1.PublisherClient(batch_settings)
        topic_path = publisher.topic_path(self.project_id, self.topic_id)
        publish_futures = []

        queue_str = f"'{self.topic_id}.{self.subscription_id}'"
        n_documents = len(documents)

        tqdm_kwargs_default = {
            "desc": f"Pushing to {queue_str}",
            "total": n_documents
        }
        tqdm_kwargs_final = {
            **tqdm_kwargs_default,
            **tqdm_kwargs
        } if tqdm_kwargs is not None else None

        pbar_it = documents if tqdm_kwargs is None else tqdm(
            documents, **tqdm_kwargs_final)

        for document in pbar_it:
            data_str = jsons.dumps(document)
            # Data must be a bytestring
            data = data_str.encode("utf-8")
            publish_future = publisher.publish(topic_path, data)
            # Non-blocking. Allow the publisher client to batch multiple messages.
            publish_future.add_done_callback(callback)
            publish_futures.append(publish_future)

        msg = f"Wait while {queue_str} finished to push {n_documents} messages"
        logging.info(msg)
        responses = futures.wait(publish_futures,
                                 return_when=futures.ALL_COMPLETED)
        results = [bool(x) for x in responses]

        n_success = sum(results)
        msg = f"{queue_str} Pushes {n_success}/{n_documents} messages🟢"
        logging.info(msg)
        return results

    def pop(self) -> dict:
        """read the last message"""
        subscriber = pubsub_v1.SubscriberClient()

        data = {}
        # Wrap the subscriber in a 'with' block to automatically call close() to
        # close the underlying gRPC channel when done.
        subscription_path = subscriber.subscription_path(
            self.project_id, self.subscription_id)

        # The subscriber pulls a specific number of messages. The actual
        # number of messages pulled may be smaller than max_messages.
        response = subscriber.pull(subscription=subscription_path,
                                   max_messages=1,
                                   retry=retry.Retry(deadline=300))

        # save the acknowledges ids
        ack_ids = []
        for received_message in response.received_messages:
            data_str = received_message.message.data.decode("utf-8")
            data = jsons.loads(data_str)
            ack_ids.append(received_message.ack_id)

        # Acknowledges the received messages so they will not be sent again.
        if ack_ids:
            subscriber.acknowledge(request={
                "subscription": subscription_path,
                "ack_ids": ack_ids
            })

        subscriber.close()

        return data
