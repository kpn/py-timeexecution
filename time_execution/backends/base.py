"""
Base metrics
"""


class BaseMetricsBackend(object):
    def write(self, key, data):
        raise NotImplemented
