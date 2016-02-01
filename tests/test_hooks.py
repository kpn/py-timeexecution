import unittest

from tests.conftest import go
from time_execution import configure, time_execution
from time_execution.backends.base import BaseMetricsBackend


class AssertBackend(BaseMetricsBackend):

    def __init__(self, callback):
        self.callback = callback

    def write(self, name, **data):
        return self.callback(name, **data)


class TestTimeExecution(unittest.TestCase):

    def test_hook(self):

        def test_args(**kwargs):
            self.assertIn('response', kwargs)
            self.assertIn('exception', kwargs)
            self.assertIn('metric', kwargs)
            return dict()

        def test_metadata(*args, **kwargs):
            return dict(test_key='test value')

        def asserts(name, **data):
            self.assertEqual(data['test_key'], 'test value')

        configure(
            backends=[AssertBackend(asserts)],
            hooks=[test_args, test_metadata]
        )

        go()

    def test_hook_exception(self):

        message = 'exception message'

        def exception_hook(exception, **kwargs):
            self.assertIsInstance(exception, TimeExecutionException)
            return dict(exception_message=str(exception))

        def asserts(name, **data):
            self.assertEqual(data['exception_message'], message)

        configure(
            backends=[AssertBackend(asserts)],
            hooks=[exception_hook]
        )

        class TimeExecutionException(Exception):
            pass

        @time_execution
        def go():
            raise TimeExecutionException(message)

        with self.assertRaises(TimeExecutionException):
            go()

    def test_hook_func_args(self):
        param = 'foo'

        def hook(response, exception, metric, func_args, func_kwargs):
            self.assertEqual(func_args[0], param)

        configure(hooks=[hook])

        @time_execution
        def go(param1):
            return '200 OK'

        go(param)

    def test_hook_func_kwargs(self):
        param = 'foo'

        def hook(response, exception, metric, func_args, func_kwargs):
            self.assertEqual(func_kwargs['param1'], param)

        configure(hooks=[hook])

        @time_execution
        def go(param1):
            return '200 OK'

        go(param1=param)
