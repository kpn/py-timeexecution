import logging
from datetime import datetime

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import TransportError

from time_execution.backends.base import BaseMetricsBackend

logger = logging.getLogger(__name__)


class ElasticsearchBackend(BaseMetricsBackend):
    def __init__(
        self,
        hosts=None,
        index="metrics",
        index_pattern="{index}-{date:%Y.%m.%d}",
        pipeline=None,
        *args,
        **kwargs,
    ):
        # Assign these in the backend as they are needed when writing metrics
        # to elasticsearch
        self.index = index
        self.index_pattern = index_pattern
        self.pipeline = pipeline

        # setup the client
        self.client = Elasticsearch(hosts=hosts, *args, **kwargs)

    def get_index(self):
        return self.index_pattern.format(index=self.index, date=datetime.now())

    def write(self, name, **data):
        """
        Write the metric to elasticsearch

        Args:
            name (str): The name of the metric to write
            data (dict): Additional data to store with the metric
        """

        data["name"] = name
        if not ("timestamp" in data):
            data["timestamp"] = datetime.utcnow()

        try:
            index_params = {
                "index": self.get_index(),
                "id": None,
                "body": data,
            }
            if self.pipeline:
                index_params["pipeline"] = self.pipeline

            self.client.index(**index_params)
        except TransportError as exc:
            logger.warning("writing metric %r failure %r", data, exc)

    def bulk_write(self, metrics):
        """
        Write multiple metrics to elasticsearch in one request

        Args:
            metrics (list): data with mappings to send to elasticsearch
        """
        actions = []
        index = self.get_index()
        for metric in metrics:
            actions.append({"index": {"_index": index}})
            actions.append(metric)

        bulk_params = {"operations": actions}
        if self.pipeline:
            bulk_params["pipeline"] = self.pipeline

        try:
            self.client.bulk(**bulk_params)
        except TransportError as exc:
            logger.warning("bulk_write metrics %r failure %r", metrics, exc)
