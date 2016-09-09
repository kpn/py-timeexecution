from __future__ import absolute_import

import logging
from datetime import datetime

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import TransportError
from time_execution.backends.base import BaseMetricsBackend

logger = logging.getLogger(__file__)


class ElasticsearchBackend(BaseMetricsBackend):
    def __init__(self, hosts=None, index="metrics", doc_type="metric",
                 index_pattern="{index}-{date:%Y.%m.%d}", *args, **kwargs):
        # Assign these in the backend as they are needed when writing metrics
        # to elasticsearch
        self.index = index
        self.doc_type = doc_type
        self.index_pattern = index_pattern

        # setup the client
        self.client = Elasticsearch(hosts=hosts, *args, **kwargs)

        # ensure the index is created
        try:
            self._setup_index()
        except TransportError as exc:
            logger.error('index setup error %r', exc)
        try:
            self._setup_mapping()
        except TransportError as exc:
            logger.error('mapping setup error %r', exc)

    def get_index(self):
        return self.index_pattern.format(index=self.index, date=datetime.now())

    def _setup_index(self):
        return self.client.indices.create(self.index, ignore=400)

    def _setup_mapping(self):
        return self.client.indices.put_template(
            name="timeexecution-{}".format(self.index),
            body={
                "template": "{}*".format(self.index),
                "mappings": {
                    self.doc_type: {
                        "dynamic_templates": [
                            {
                                "strings": {
                                    "mapping": {
                                        "index": "not_analyzed",
                                        "omit_norms": True,
                                        "type": "string"
                                    },
                                    "match_mapping_type": "string"
                                }
                            }
                        ],
                        "_source": {
                            "enabled": True
                        },
                        "properties": {
                            "name": {
                                "type": "string",
                                "index": "not_analyzed"
                            },
                            "timestamp": {
                                "type": "date",
                                "index": "not_analyzed"
                            },
                            "hostname": {
                                "type": "string",
                                "index": "not_analyzed"
                            },
                            "value": {
                                "type": "float",
                                "index": "not_analyzed"
                            },
                            "origin": {
                                "type": "string",
                                "index": "not_analyzed"
                            },
                        }
                    },
                },
                "settings": {
                    "number_of_shards": "1",
                    "number_of_replicas": "0",
                },
            }
        )

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
            self.client.index(
                index=self.get_index(),
                doc_type=self.doc_type,
                id=None,
                body=data
            )
        except TransportError as exc:
            logger.warning('writing metric %r failure %r', data, exc)

    def bulk_write(self, metrics):
        """
        Write multiple metrics to elasticsearch in one request

        Args:
            metrics (list): data with mappings to send to elasticsearch
        """
        actions = []
        index = self.get_index()
        for metric in metrics:
            actions.append({'index': {'_index': index, '_type': self.doc_type}})
            actions.append(metric)
        try:
            self.client.bulk(actions)
        except TransportError as exc:
            logger.warning('bulk_write metrics %r failure %r', metrics, exc)
