"""
Base metrics backend
"""


class BaseMetricsBackend:
    def write(self, name, **data):
        raise NotImplementedError

    def bulk_write(self, metrics):
        raise NotImplementedError
