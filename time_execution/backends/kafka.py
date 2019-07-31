from __future__ import absolute_import

import logging
from datetime import datetime

from kafka import KafkaProducer
from kafka.errors import KafkaTimeoutError, NoBrokersAvailable
from time_execution.backends.base import BaseMetricsBackend
from time_execution.serializer import JSONSerializer

logger = logging.getLogger(__name__)


class KafkaBackend(BaseMetricsBackend):
    def __init__(self, hosts=None, topic=None, serializer_class=JSONSerializer, *args, **kwargs):
        """
        :param hosts:
        :param topic:
        :param serializer_class: to be used as value serializer
        :param args:
        :param kwargs: extra parameters that will be passed to the backend
        """
        self.hosts = hosts or []
        self.topic = topic
        self._producer = None
        self._kwargs = kwargs
        self._serializer_class = serializer_class

        try:
            self.producer
        except NoBrokersAvailable as exc:
            logger.error('client setup error %r', exc)

    @property
    def producer(self):
        """
        :raises: kafka.errors.NoBrokersAvailable if the connection is broken
        """
        if self._producer:
            return self._producer

        self._producer = KafkaProducer(
            bootstrap_servers=self.hosts,
            value_serializer=lambda v: self._serializer_class().dumps(v).encode('utf-8'),
            **self._kwargs
        )

        return self._producer

    def write(self, name, **data):
        """
        Write the metric to kafka

        Args:
            name (str): The name of the metric to write
            data (dict): Additional data to store with the metric
        """

        data["name"] = name
        if not ("timestamp" in data):
            data["timestamp"] = datetime.utcnow()

        try:
            self.producer.send(topic=self.topic, value=data)
            self.producer.flush()
        except (KafkaTimeoutError, NoBrokersAvailable) as exc:
            logger.warning('writing metric %r failure %r', data, exc)

    def bulk_write(self, metrics):
        """
        Write multiple metrics to kafka in one request

        Args:
            metrics (list):
        """
        try:
            for metric in metrics:
                self.producer.send(self.topic, metric)
            self.producer.flush()
        except (KafkaTimeoutError, NoBrokersAvailable) as exc:
            logger.warning('bulk_write metrics %r failure %r', metrics, exc)
