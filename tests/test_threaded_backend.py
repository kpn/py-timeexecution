import time
from datetime import datetime

import mock
from freezegun import freeze_time
from tests.conftest import go
from tests.test_base_backend import TestBaseBackend
from time_execution import settings
from time_execution.backends import base, elasticsearch
from time_execution.backends.threaded import ThreadedBackend
from time_execution.decorator import SHORT_HOSTNAME

from .test_elasticsearch import ElasticTestMixin


class TestTimeExecution(TestBaseBackend):

    def setUp(self):
        self.qsize = 4
        self.qtimeout = 0.1

        self.mocked_backend = mock.Mock(spec=base.BaseMetricsBackend)
        self.MockedBackendClass = mock.Mock(return_value=self.mocked_backend)

        self.backend = ThreadedBackend(
            self.MockedBackendClass,
            backend_args=('arg1', 'arg2'),
            backend_kwargs=dict(key1='kwarg1', key2='kwarg2'),
            queue_maxsize=self.qsize,
            queue_timeout=self.qtimeout,
        )
        settings.configure(backends=[self.backend])

    def test_backend_args(self):
        self.MockedBackendClass.assert_called_with('arg1', 'arg2', key1='kwarg1', key2='kwarg2')
        ThreadedBackend(self.MockedBackendClass)
        self.MockedBackendClass.assert_called_with()

    def test_empty_queue(self):
        time.sleep(2 * self.qtimeout)  # ensures queue.get times out
        self.assertEqual(0, self.backend.fetched_items)

    def test_decorator(self):
        with freeze_time('2016-08-01 00:00:00'):
            go()
        # ensure worker thread catches up
        time.sleep(2 * self.qtimeout)
        mocked_write = self.mocked_backend.write
        mocked_write.assert_called_with(
            'tests.conftest.go',
            hostname=SHORT_HOSTNAME,
            timestamp=datetime(2016, 8, 1),
            value=0.0)
        self.assertEqual(1, self.backend.fetched_items)

    def test_double_start(self):
        self.assertEqual(0, self.backend.fetched_items)
        go()
        time.sleep(2 * self.qtimeout)
        self.assertEqual(1, self.backend.fetched_items)
        # try to double start
        self.backend.start_worker()
        self.assertEqual(1, self.backend.fetched_items)

    def test_write_error(self):
        self.mocked_backend.write.side_effect = RuntimeError('mocked')
        go()
        time.sleep(2 * self.qtimeout)

    def test_queue_congestion(self):
        # assure worker is stopped
        self.backend.worker_limit = 0
        time.sleep(self.qtimeout)
        self.assertEqual(self.backend.thread, None)

        # fill in the queue
        for _ in range(self.qsize * 2):
            go()
        self.assertTrue(self.backend._queue.full())

        # resume the worker
        self.backend.worker_limit = None
        self.backend.start_worker()
        time.sleep(self.qsize * self.qtimeout)  # assure all metrics are picked up

        self.assertEqual(self.qsize, len(self.mocked_backend.write.call_args_list))


class TestElastic(TestBaseBackend, ElasticTestMixin):

    def setUp(self):
        self.qtime = 0.1
        self.backend = ThreadedBackend(
            elasticsearch.ElasticsearchBackend,
            backend_args=('elasticsearch', ),
            backend_kwargs=dict(index='threaded-metrics'),
            queue_timeout=self.qtime,
        )
        settings.configure(backends=[self.backend])
        self._clear(self.backend.backend)

    def test_write_method(self):
        go()
        time.sleep(2 * self.qtime)
        metrics = self._query_backend(self.backend.backend, go.fqn)
        self.assertEqual(metrics['hits']['total'], 1)
