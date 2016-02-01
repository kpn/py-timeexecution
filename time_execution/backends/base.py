"""
Base metrics backend
"""


class BaseMetricsBackend(object):
    def write(self, name, **data):
        raise NotImplementedError
