import random
import string
import unittest
from datetime import datetime

import mock
from elasticsearch.serializer import JSONSerializer
from fqn_decorators import get_fqn
from freezegun import freeze_time
from kafka import KafkaConsumer, TopicPartition
from kafka.errors import KafkaTimeoutError
from tests.conftest import Dummy, go
from time_execution import settings
from time_execution.backends.kafka import KafkaBackend

KAFKA_HOST = 'kafka'


def random_string(length):
    return "".join(random.choice(string.ascii_letters) for i in range(length))


class TestConnectionErrors(unittest.TestCase):
    @mock.patch('time_execution.backends.kafka.logger')
    def test_error_resilience(self, mocked_logger):
        backend = KafkaBackend(hosts=['non-existant-domain'], topic='prod')
        assert len(mocked_logger.error.call_args_list) == 1

        # ensure write failure is caught and logged
        backend.write(name='test_error_resilience')
        mocked_logger.warning.assert_called_once()


class TestTimeExecution(unittest.TestCase):
    def setUp(self):
        super(TestTimeExecution, self).setUp()

        self.topic = random_string(5)

        self.backend = KafkaBackend(KAFKA_HOST, topic=self.topic)
        settings.configure(backends=[self.backend])

    def _query_backend(self):
        consumer = KafkaConsumer(
            bootstrap_servers=KAFKA_HOST, value_deserializer=lambda v: JSONSerializer().loads(v.decode('utf-8'))
        )

        tp = TopicPartition(self.topic, 0)
        consumer.assign([tp])

        count = consumer.position(tp)

        consumer.seek(tp, 0)

        metrics = []
        for i in range(count):
            metrics.append(next(consumer))

        return metrics

    def test_time_execution(self):

        count = 4

        for i in range(count):
            go()

        metrics = self._query_backend()
        assert len(metrics) == count

        for metric in metrics:
            assert metric.value

    def test_duration_field(self):
        with settings(duration_field='my_duration'):
            go()
            for metric in self._query_backend():
                assert 'my_duration' in metric.value

    def test_with_arguments(self):
        go('hello', world='world')
        Dummy().go('hello', world='world')

        metrics = self._query_backend()

        assert len([m for m in metrics if m.value['name'] == get_fqn(go)]) == 1
        assert len([m for m in metrics if m.value['name'] == get_fqn(Dummy().go)]) == 1

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
            for metric in self._query_backend():
                assert metric.value['test_key'] == 'test value'

    def test_with_origin(self):
        with settings(origin='unit_test'):

            go()

            for metric in self._query_backend():
                assert metric.value['origin'] == 'unit_test'

    def test_bulk_write(self):
        metrics = [
            {'name': 'metric.name', 'value': 1, 'timestamp': 1},
            {'name': 'metric.name', 'value': 2, 'timestamp': 2},
            {'name': 'metric.name', 'value': 3, 'timestamp': 3},
        ]
        self.backend.bulk_write(metrics)
        query_result = self._query_backend()
        self.assertEqual(len(metrics), len(query_result))

    @mock.patch('time_execution.backends.kafka.logger')
    def test_write_error_warning(self, mocked_logger):
        transport_error = KafkaTimeoutError('mocked error')
        es_index_error_ctx = mock.patch(
            'time_execution.backends.kafka.KafkaProducer.send', side_effect=transport_error
        )
        frozen_time_ctx = freeze_time('2016-07-13')

        with es_index_error_ctx, frozen_time_ctx:
            self.backend.write(name='test:metric', value=None)
            mocked_logger.warning.assert_called_once_with(
                'writing metric %r failure %r',
                {'timestamp': datetime(2016, 7, 13), 'value': None, 'name': 'test:metric'},
                transport_error,
            )

    @mock.patch('time_execution.backends.kafka.logger')
    def test_bulk_write_error(self, mocked_logger):
        transport_error = KafkaTimeoutError('mocked error')
        es_index_error_ctx = mock.patch(
            'time_execution.backends.kafka.KafkaProducer.send', side_effect=transport_error
        )
        metrics = [1, 2, 3]
        with es_index_error_ctx:
            self.backend.bulk_write(metrics)
            mocked_logger.warning.assert_called_once_with('bulk_write metrics %r failure %r', metrics, transport_error)
