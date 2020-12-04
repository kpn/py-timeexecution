#!/usr/bin/env python
import os
import sys

# make sure we can import time_execution library
path = os.path.dirname(os.path.abspath(__file__))
sys.path.append("/".join(path.split("/")[:-1]))

from time_execution.backends.base import BaseMetricsBackend  # noqa isort:skip
from time_execution.backends.threaded import ThreadedBackend  # noqa isort:skip


class DummyBackend(BaseMetricsBackend):
    def write(self, name, **data):
        pass


ThreadedBackend(DummyBackend, queue_timeout=1)
