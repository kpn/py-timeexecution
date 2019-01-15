from __future__ import absolute_import

import datetime
import logging
import threading
import time
from multiprocessing import Queue

from time_execution.backends.base import BaseMetricsBackend

try:
    from Queue import Empty, Full
except ImportError:
    from queue import Empty, Full


logger = logging.getLogger(__file__)


class ThreadedBackend(BaseMetricsBackend):

    def __init__(self, backend, backend_args=None, backend_kwargs=None,
                 queue_maxsize=1000, queue_timeout=0.5, worker_limit=None,
                 lazy_init=False):
        if backend_args is None:
            backend_args = tuple()
        if backend_kwargs is None:
            backend_kwargs = dict()
        self.parent_thread = None
        self.queue_timeout = queue_timeout
        self.worker_limit = worker_limit
        self.thread = None
        self.fetched_items = 0
        self.bulk_size = 50
        self.bulk_timeout = 1  # second
        self.backend = backend(*backend_args, **backend_kwargs)
        self._queue = None
        self.queue_maxsize = queue_maxsize
        self.lazy_init = lazy_init
        if not lazy_init:
            self.start_worker()

    def write(self, name, **data):
        if self.lazy_init and not self.thread:
            self.start_worker()

        data["timestamp"] = datetime.datetime.utcnow()
        try:
            self._queue.put_nowait((name, data))
        except Full:
            logger.warning("Discard metric %s", name)

    def start_worker(self):
        if self.thread:
            return

        self.parent_thread = threading.current_thread()
        if not self._queue:
            self._queue = Queue(maxsize=self.queue_maxsize)
        self.fetched_items = 0
        self.thread = threading.Thread(
            target=self.worker,
            name="TimeExecutionThread"
        )
        self.thread.daemon = False
        self.thread.start()

    def batch_ready(self, batch):
        return self.bulk_size < len(batch)

    def batch_time(self, last_write):
        return (time.time() - last_write) >= self.bulk_timeout

    def has_work(self):
        if self.worker_limit is None:
            return True
        return self.fetched_items < self.worker_limit

    def worker(self):
        metrics = []
        last_write = time.time()

        def send_metrics():
            try:
                self.backend.bulk_write(metrics)
            except Exception as exc:
                logger.warning('%r write failure %r', self.backend, exc)

        while self.has_work():
            if self.batch_ready(metrics) or (self.batch_time(last_write) and metrics):
                send_metrics()
                last_write = time.time()
                metrics = []
            try:
                name, data = self._queue.get(True, self.queue_timeout)
            except Empty:
                if not self.parent_thread.is_alive():
                    return
                continue
            except TypeError as err:
                logger.warning('stopping the worker due to %r', err)
                break
            self.fetched_items += 1
            data['name'] = name
            metrics.append(data)
        if metrics:
            send_metrics()
        self.thread = None
