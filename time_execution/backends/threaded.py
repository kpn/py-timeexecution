from __future__ import absolute_import

import datetime
import logging
import threading

from time_execution.backends.base import BaseMetricsBackend

try:
    from Queue import Queue, Empty, Full
except ImportError:
    from queue import Queue, Empty, Full


logger = logging.getLogger(__file__)


class ThreadedBackend(BaseMetricsBackend):

    def __init__(self, backend, backend_args=None, backend_kwargs=None,
                 queue_maxsize=1000, queue_timeout=0.5, worker_limit=None):
        if backend_args is None:
            backend_args = tuple()
        if backend_kwargs is None:
            backend_kwargs = dict()
        self.queue_timeout = queue_timeout
        self.worker_limit = worker_limit
        self.thread = None
        self.fetched_items = 0
        self.backend = backend(*backend_args, **backend_kwargs)
        self._queue = Queue(maxsize=queue_maxsize)
        self.start_worker()

    def write(self, name, **data):
        data["timestamp"] = datetime.datetime.utcnow()
        try:
            self._queue.put_nowait((name, data))
        except Full:
            logger.warning("Discard metric %s", name)

    def start_worker(self):
        if self.thread:
            return
        self.fetched_items = 0
        self.thread = threading.Thread(target=self.worker)
        self.thread.daemon = True
        self.thread.start()

    def worker(self):
        while (self.worker_limit is None) or self.fetched_items < (self.worker_limit - 1):
            try:
                name, data = self._queue.get(True, self.queue_timeout)  # blocking get
            except Empty:
                continue
            self.fetched_items += 1
            try:
                self.backend.write(name, **data)
            except Exception as exc:
                logger.warning('%r write failure %r', self.backend, exc)
        self.thread = None
