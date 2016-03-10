from __future__ import absolute_import

from datetime import datetime

from elasticsearch import Elasticsearch
from time_execution.backends.base import BaseMetricsBackend


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
        self._setup_index()
        self._setup_mapping()

    def get_index(self):
        return self.index_pattern.format(index=self.index, date=datetime.now())

    def _setup_index(self):
        return self.client.indices.create(self.index, ignore=400)

    def _setup_mapping(self):
        return self.client.indices.put_template(
            name="timeexecution",
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
        data["timestamp"] = datetime.utcnow()

        self.client.index(
            index=self.get_index(),
            doc_type=self.doc_type,
            id=None,
            body=data
        )
