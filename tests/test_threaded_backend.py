import time
from datetime import datetime

import mock
from freezegun import freeze_time
from tests.conftest import go
from tests.test_base_backend import TestBaseBackend
from time_execution import settings
from time_execution.backends import elasticsearch
from time_execution.backends.threaded import ThreadedBackend
from time_execution.decorator import SHORT_HOSTNAME

from .test_elasticsearch import ElasticTestMixin


class TestTimeExecution(TestBaseBackend):

    def setUp(self):
        self.qsize = 10
        self.qtimeout = 0.1

        self.mocked_backend = mock.Mock(spec=elasticsearch.ElasticsearchBackend)
        self.MockedBackendClass = mock.Mock(return_value=self.mocked_backend)

        self.backend = ThreadedBackend(
            self.MockedBackendClass,
            backend_args=('arg1', 'arg2'),
            backend_kwargs=dict(key1='kwarg1', key2='kwarg2'),
            queue_maxsize=self.qsize,
            queue_timeout=self.qtimeout,
        )
        self.backend.bulk_size = self.qsize / 2
        self.backend.bulk_timeout = self.qtimeout * 2
        settings.configure(backends=[self.backend])

    def stop_worker(self):
        self.backend.worker_limit = 0
        time.sleep(self.qtimeout * 2)
        self.assertEqual(self.backend.thread, None)

    def resume_worker(self, worker_limit=None, **kwargs):
        self.backend.worker_limit = worker_limit
        for key, val in kwargs.items():
            if hasattr(self.backend, key):
                setattr(self.backend, key, val)
        self.backend.start_worker()

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
        time.sleep(2 * self.backend.bulk_timeout)
        mocked_write = self.mocked_backend.bulk_write
        self.assertEqual(1, self.backend.fetched_items)
        mocked_write.assert_called_with([{
            'timestamp': datetime(2016, 8, 1, 0, 0),
            'hostname': SHORT_HOSTNAME,
            'name': 'tests.conftest.go',
            'value': 0.0,
        }])

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
        self.stop_worker()

        # fill in the queue
        for _ in range(self.qsize * 2):
            go()
        self.assertTrue(self.backend._queue.full())

        self.resume_worker(bulk_timeout=self.qtimeout)
        # wait until all metrics are picked up
        time.sleep(self.qsize * self.qtimeout)
        # check that metrics in the queue were sent with bulk_write calls
        call_args_list = self.mocked_backend.bulk_write.call_args_list
        self.assertEqual(
            self.qsize,
            sum(len(args[0]) for args, _ in call_args_list)
        )

    def test_worker_sends_remainder(self):
        self.stop_worker()
        self.mocked_backend.bulk_write.side_effect = RuntimeError('mock')
        loops_count = 3
        self.assertTrue(loops_count < self.backend.bulk_size)
        for _ in range(loops_count):
            go()
        self.backend.worker_limit = loops_count
        self.backend.worker()
        self.assertEqual(loops_count, self.backend.fetched_items)
        mocked_bulk_write = self.mocked_backend.bulk_write
        mocked_bulk_write.assert_called_once()
        self.assertEqual(
            loops_count,
            len(mocked_bulk_write.call_args[0][0])
        )

    def test_worker_error(self):
        self.assertFalse(self.backend.thread is None)
        # simulate TypeError in queue.get
        with mock.patch.object(self.backend._queue, 'get', side_effect=TypeError):
            # ensure worker loop repeat
            time.sleep(2 * self.qtimeout)
        # assert thread stopped
        self.assertTrue(self.backend.thread is None)


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
        time.sleep(2 * self.backend.bulk_timeout)
        metrics = self._query_backend(self.backend.backend, go.fqn)
        self.assertEqual(metrics['hits']['total'], 1)
