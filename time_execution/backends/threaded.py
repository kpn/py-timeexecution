import datetime
import logging
import threading
import time
from importlib import import_module
from multiprocessing import Queue
from queue import Empty, Full

from time_execution.backends.base import BaseMetricsBackend

logger = logging.getLogger(__name__)


def import_from_string(val):
    """
    Attempt to import a class from a string representation.
    """
    try:
        module_path, class_name = val.rsplit(".", 1)
        module = import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        msg = "Could not import metric agent '%s' for ThreadedBackend. %s: %s." % (val, e.__class__.__name__, e)
        raise ImportError(msg)


class ThreadedBackend(BaseMetricsBackend):
    def __init__(
        self,
        backend,
        backend_args=None,
        backend_kwargs=None,
        queue_maxsize=1000,
        queue_timeout=0.5,
        worker_limit=None,
        bulk_size=50,
        bulk_timeout=1,
    ):
        if backend_args is None:
            backend_args = tuple()
        if backend_kwargs is None:
            backend_kwargs = dict()
        self.parent_thread = threading.current_thread()
        self.queue_timeout = queue_timeout
        self.worker_limit = worker_limit
        self.thread = None
        self.fetched_items = 0
        self.bulk_size = bulk_size
        self.bulk_timeout = bulk_timeout

        if isinstance(backend, str):
            backend = import_from_string(backend)

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
        self.thread = threading.Thread(target=self.worker, name="TimeExecutionThread")
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
                logger.warning("%r write failure %r", self.backend, exc)

        while self.has_work():
            if self.batch_ready(metrics) or (self.batch_time(last_write) and metrics):
                send_metrics()
                last_write = time.time()
                metrics = []
            try:
                name, data = self._queue.get(True, self.queue_timeout)
            except Empty:
                if not self.parent_thread.is_alive():
                    break
                continue
            except TypeError as err:
                logger.warning("stopping the worker due to %r", err)
                break
            self.fetched_items += 1
            data["name"] = name
            metrics.append(data)
        if metrics:
            send_metrics()
        self.thread = None
