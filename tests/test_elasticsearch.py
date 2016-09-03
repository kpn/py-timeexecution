from datetime import datetime

import mock
from elasticsearch.exceptions import TransportError
from fqn_decorators import get_fqn
from freezegun import freeze_time
from tests.conftest import Dummy, go
from tests.test_base_backend import TestBaseBackend
from time_execution import settings
from time_execution.backends.elasticsearch import ElasticsearchBackend


class TestConnectionErrors(TestBaseBackend):

    @mock.patch('time_execution.backends.elasticsearch.logger')
    def test_error_resilience(self, mocked_logger):
        backend = ElasticsearchBackend(hosts=['non-existant-domain'])
        # ensure index and mapping setup failures are caught and logged
        self.assertEqual(2, len(mocked_logger.error.call_args_list))
        # ensure write failure is caught and logged
        backend.write(name='test_error_resilience')
        mocked_logger.warning.assert_called_once()


class ElasticTestMixin(object):

    @staticmethod
    def _clear(backend):
        backend.client.indices.delete(backend.index, ignore=404)
        backend.client.indices.delete("{}*".format(backend.index), ignore=404)

    @staticmethod
    def _query_backend(backend, name):
        backend.client.indices.refresh(backend.get_index())
        metrics = backend.client.search(
            index=backend.get_index(),
            body={
                "query": {
                    "term": {"name": name}
                },
            }
        )
        return metrics


class TestTimeExecution(TestBaseBackend):
    def setUp(self):
        super(TestTimeExecution, self).setUp()

        self.backend = ElasticsearchBackend(
            'elasticsearch',
            index='unittest',
        )
        settings.configure(backends=[self.backend])
        self._clear()

    def tearDown(self):
        self._clear()

    def _clear(self):
        ElasticTestMixin._clear(self.backend)

    def _query_backend(self, name):
        return ElasticTestMixin._query_backend(self.backend, name)

    def test_time_execution(self):

        count = 4

        for i in range(count):
            go()

        metrics = self._query_backend(go.fqn)
        self.assertEqual(metrics['hits']['total'], count)

        for metric in metrics['hits']['hits']:
            self.assertTrue('value' in metric['_source'])
            self.assertFalse('origin' in metric['_source'])

    def test_duration_field(self):
        with settings(duration_field='my_duration'):
            go()
            for metric in self._query_backend(go.fqn)['hits']['hits']:
                self.assertTrue('my_duration' in metric['_source'])

    def test_with_arguments(self):
        go('hello', world='world')
        Dummy().go('hello', world='world')

        metrics = self._query_backend(get_fqn(go))
        self.assertEqual(metrics['hits']['total'], 1)

        metrics = self._query_backend(get_fqn(Dummy().go))
        self.assertEqual(metrics['hits']['total'], 1)

    def test_hook(self):

        def test_args(**kwargs):
            self.assertIn('response', kwargs)
            self.assertIn('exception', kwargs)
            self.assertIn('metric', kwargs)
            return dict()

        def test_metadata(*args, **kwargs):
            return dict(test_key='test value')

        with settings(hooks=[test_args, test_metadata]):
            go()
            for metric in self._query_backend(go.fqn)['hits']['hits']:
                self.assertEqual(metric['_source']['test_key'], 'test value')

    @mock.patch('time_execution.backends.elasticsearch.logger')
    def test_error_warning(self, mocked_logger):

        transport_error = TransportError('mocked error')
        es_index_error_ctx = mock.patch(
            'time_execution.backends.elasticsearch.Elasticsearch.index',
            side_effect=transport_error
        )
        frozen_time_ctx = freeze_time('2016-07-13')

        with es_index_error_ctx, frozen_time_ctx:
            self.backend.write(name='test:metric', value=None)
            mocked_logger.warning.assert_called_once_with(
                'writing metric %r failure %r',
                {
                    'timestamp': datetime(2016, 7, 13),
                    'value': None,
                    'name': 'test:metric'
                },
                transport_error
            )

    def test_with_origin(self):
        with settings(origin='unit_test'):

            go()

            for metric in self._query_backend(go.fqn)['hits']['hits']:
                self.assertEqual(metric['_source']['origin'], 'unit_test')

    def test_bulk_write(self):
        metrics = [
            {
                'name': 'metric.name',
                'value': 1,
                'timestamp': 1,
            },
            {
                'name': 'metric.name',
                'value': 2,
                'timestamp': 2,
            },
            {
                'name': 'metric.name',
                'value': 3,
                'timestamp': 3,
            }
        ]
        self.backend.bulk_write(metrics)
        query_result = self._query_backend('metric.name')
        self.assertEqual(
            len(metrics),
            query_result['hits']['total']
        )

    @mock.patch('time_execution.backends.elasticsearch.logger')
    def test_bulk_write_error(self, mocked_logger):
        transport_error = TransportError('mocked error')
        es_index_error_ctx = mock.patch(
            'time_execution.backends.elasticsearch.Elasticsearch.bulk',
            side_effect=transport_error
        )
        metrics = [1, 2, 3]
        with es_index_error_ctx:
            self.backend.bulk_write(metrics)
            mocked_logger.warning.assert_called_once_with(
                'bulk_write metrics %r failure %r',
                metrics,
                transport_error)
