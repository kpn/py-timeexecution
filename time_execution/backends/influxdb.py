from __future__ import absolute_import

import socket

from influxdb.influxdb08 import InfluxDBClient
from time_execution.backends.base import BaseMetricsBackend

SHORT_HOSTNAME = socket.gethostname()


class InfluxBackend(BaseMetricsBackend):
    def __init__(self, **kwargs):
        kwargs.setdefault('use_udp', True)
        self.client = InfluxDBClient(**kwargs)

    def write(self, name, **data):
        self.client.write_points([{
            "name": name,
            "columns": list(data.keys()),
            "points": [list(data.values())]
        }])
