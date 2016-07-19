from fqn_decorators import get_fqn
from influxdb.influxdb08.client import InfluxDBClientError
from tests.conftest import Dummy, go
from tests.test_base_backend import TestBaseBackend
from time_execution import settings
from time_execution.backends.influxdb import InfluxBackend


class TestTimeExecution(TestBaseBackend):
    def setUp(self):
        super(TestTimeExecution, self).setUp()

        self.database = 'unittest'
        self.backend = InfluxBackend(
            host='influx',
            database=self.database,
            use_udp=False
        )

        try:
            self.backend.client.create_database(self.database)
        except InfluxDBClientError:
            # Something blew up so ignore it
            pass

        settings.configure(backends=[self.backend])

    def tearDown(self):
        self.backend.client.delete_database(self.database)

    def _query_backend(self, name):
        query = 'select * from {}'.format(name)
        metrics = self.backend.client.query(query)[0]
        for metric in metrics['points']:
            yield dict(zip(metrics['columns'], metric))

    def test_time_execution(self):
        count = 4
        for i in range(count):
            go()

        metrics = list(self._query_backend(go.fqn))
        self.assertEqual(len(metrics), count)

        for metric in metrics:
            self.assertTrue('value' in metric)
            self.assertFalse('origin' in metric)

    def test_duration_field(self):

        with settings(duration_field='my_duration'):
            go()

            for metric in self._query_backend(go.fqn):
                self.assertTrue('my_duration' in metric)

    def test_with_arguments(self):
        go('hello', world='world')
        Dummy().go('hello', world='world')

        metrics = list(self._query_backend(get_fqn(go)))
        self.assertEqual(len(metrics), 1)

        metrics = list(self._query_backend(get_fqn(Dummy().go)))
        self.assertEqual(len(metrics), 1)

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

            for metric in self._query_backend(go.fqn):
                self.assertEqual(metric['test_key'], 'test value')

    def test_with_origin(self):
        with settings(origin='unit_test'):

            go()

            for metric in self._query_backend(go.fqn):
                self.assertEqual(metric['origin'], 'unit_test')
