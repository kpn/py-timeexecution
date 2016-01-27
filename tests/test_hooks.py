import unittest

from tests.conftest import go
from time_execution import configure, time_execution


class TestTimeExecution(unittest.TestCase):

    def test_hook(self):

        def test_args(**kwargs):
            self.assertIn('response', kwargs)
            self.assertIn('exception', kwargs)
            self.assertIn('metric', kwargs)
            return dict()

        def test_metadata(*args, **kwargs):
            return dict(test_key='test value')

        configure(hooks=[test_args, test_metadata])

        go()

    def test_hook_exception(self):

        def exception_hook(exception, **kwargs):
            self.assertTrue(exception)
            return dict(exception_message=str(exception))

        configure(hooks=[exception_hook])

        class TimeExecutionException(Exception):
            message = 'default'

        @time_execution
        def go():
            raise TimeExecutionException('test exception')

        with self.assertRaises(TimeExecutionException):
            go()

    def test_hook_func_args(self):
        param = 'foo'

        def hook(response, exception, metric, func_args, func_kwargs):
            self.assertEqual(func_args[0], param)
            return metric

        configure(hooks=[hook])

        @time_execution
        def go(param1):
            return '200 OK'

        go(param)

    def test_hook_func_kwargs(self):
        param = 'foo'

        def hook(response, exception, metric, func_args, func_kwargs):
            self.assertEqual(func_kwargs['param1'], param)
            return metric

        configure(hooks=[hook])

        @time_execution
        def go(param1):
            return '200 OK'

        go(param1=param)
