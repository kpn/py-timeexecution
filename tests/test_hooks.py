import pytest
from fqn_decorators import get_fqn

from tests.conftest import go
from time_execution import GeneratorHookReturnType, settings, time_execution, time_execution_async
from time_execution.backends.base import BaseMetricsBackend


class AssertBackend(BaseMetricsBackend):
    def __init__(self, callback):
        self.callback = callback

    def write(self, name, **data):
        return self.callback(name, **data)


class CollectorBackend(BaseMetricsBackend):
    def __init__(self):
        self.metrics = []

    def write(self, name, **data):
        self.metrics.append({name: data})

    def clean(self):
        self.metrics = []


def local_hook(**kwargs):
    return dict(local_hook_key="local hook value")


async def async_local_hook(**kwargs):
    return dict(async_local_hook="async_local_hook value")


async def async_global_hook(**kwargs):
    return dict(async_global_hook="async_global_hook value")


def global_hook(**kwargs):
    return dict(global_hook_key="global hook value")


class TestAsyncHooks:
    pytestmark = pytest.mark.asyncio

    async def test_async_hooks(self):
        with settings(backends=[CollectorBackend()], hooks=[global_hook, async_global_hook]):
            collector = settings.backends[0]

            @time_execution_async(extra_hooks=[local_hook, async_local_hook])
            async def func_local_hook(*args, **kwargs):
                return True

            await func_local_hook()

            assert len(collector.metrics) == 1
            metadata = collector.metrics[0][func_local_hook.get_fqn()]
            assert metadata["local_hook_key"] == "local hook value"
            assert metadata["global_hook_key"] == "global hook value"
            assert metadata["async_local_hook"] == "async_local_hook value"
            assert metadata["async_global_hook"] == "async_global_hook value"
            collector.clean()


class TestTimeExecution:
    def test_custom_hook(self):
        with settings(backends=[CollectorBackend()], hooks=[global_hook]):
            collector = settings.backends[0]

            @time_execution(extra_hooks=[local_hook])
            def func_local_hook(*args, **kwargs):
                return True

            func_local_hook()
            assert len(collector.metrics) == 1
            metadata = collector.metrics[0][func_local_hook.get_fqn()]
            assert metadata["local_hook_key"] == "local hook value"
            assert metadata["global_hook_key"] == "global hook value"
            collector.clean()

            @time_execution(extra_hooks=[local_hook], disable_default_hooks=True)
            def func_local_hook_disable_default_hooks(*args, **kwargs):
                return True

            func_local_hook_disable_default_hooks()
            assert len(collector.metrics) == 1
            metadata = collector.metrics[0][func_local_hook_disable_default_hooks.get_fqn()]
            assert metadata["local_hook_key"] == "local hook value"
            assert "global_hook_key" not in metadata
            collector.clean()

            @time_execution
            def func_global_hook(*args, **kwargs):
                return True

            func_global_hook()
            assert len(collector.metrics) == 1
            metadata = collector.metrics[0][func_global_hook.get_fqn()]
            assert metadata["global_hook_key"] == "global hook value"
            assert "local_hook_key" not in metadata
            collector.clean()

            class ClassNoHooks:
                @time_execution(extra_hooks=[local_hook])
                def method_local_hook(self):
                    return True

                @time_execution
                def method_global_hook(self):
                    return True

            ClassNoHooks().method_local_hook()
            assert len(collector.metrics) == 1
            metadata = collector.metrics[0][ClassNoHooks().method_local_hook.get_fqn()]
            assert metadata["global_hook_key"] == "global hook value"
            assert metadata["local_hook_key"] == "local hook value"
            collector.clean()

            ClassNoHooks().method_global_hook()
            assert len(collector.metrics) == 1
            metadata = collector.metrics[0][ClassNoHooks().method_global_hook.get_fqn()]
            assert metadata["global_hook_key"] == "global hook value"
            assert "local_hook_key" not in metadata
            collector.clean()

            @time_execution(extra_hooks=[local_hook])
            class ClassLocalHook:
                def method(self):
                    return True

                @time_execution
                def method_global_hook(self):
                    return True

            ClassLocalHook().method()
            assert len(collector.metrics) == 1
            metadata = collector.metrics[0][get_fqn(ClassLocalHook)]
            assert metadata["global_hook_key"] == "global hook value"
            assert metadata["local_hook_key"] == "local hook value"
            collector.clean()

            ClassLocalHook().method_global_hook()
            assert len(collector.metrics) == 2
            metadata_class = collector.metrics[0][get_fqn(ClassLocalHook)]
            assert metadata_class["local_hook_key"] == "local hook value"
            assert metadata_class["global_hook_key"] == "global hook value"
            metadata = collector.metrics[1][ClassLocalHook().method_global_hook.get_fqn()]
            assert metadata["global_hook_key"] == "global hook value"
            assert "local_hook_key" not in metadata
            collector.clean()

            @time_execution
            class ClassGlobalHook:
                def method(self):
                    return True

                @time_execution(extra_hooks=[local_hook])
                def method_local_hook(self):
                    return True

            ClassGlobalHook().method()
            assert len(collector.metrics) == 1
            metadata = collector.metrics[0][get_fqn(ClassGlobalHook)]
            assert metadata["global_hook_key"] == "global hook value"
            assert "local_hook_key" not in metadata
            collector.clean()

            ClassGlobalHook().method_local_hook()
            assert len(collector.metrics) == 2
            metadata_class = collector.metrics[0][get_fqn(ClassGlobalHook)]
            assert metadata_class["global_hook_key"] == "global hook value"
            assert "local_hook_key" not in metadata_class
            metadata = collector.metrics[1][ClassGlobalHook().method_local_hook.get_fqn()]
            assert metadata["global_hook_key"] == "global hook value"
            assert metadata["local_hook_key"] == "local hook value"
            collector.clean()

    def test_hook(self):
        def test_args(**kwargs):
            assert "response" in kwargs
            assert "exception" in kwargs
            assert "metric" in kwargs
            assert "name" in kwargs["metric"]
            return dict()

        def test_metadata(*args, **kwargs):
            return dict(test_key="test value")

        def asserts(name, **data):
            assert data["test_key"] == "test value"

        with settings(backends=[AssertBackend(asserts)], hooks=[test_args, test_metadata]):
            go()

    def test_hook_exception(self):
        message = "exception message"

        class TimeExecutionException(Exception):
            pass

        def exception_hook(exception, **kwargs):
            assert isinstance(exception, (TimeExecutionException,))
            return dict(exception_message=str(exception))

        def asserts(name, **data):
            assert data["exception_message"] == message

        @time_execution
        def go():
            raise TimeExecutionException(message)

        with settings(backends=[AssertBackend(asserts)], hooks=[exception_hook]):
            with pytest.raises(TimeExecutionException):
                go()

    def test_hook_exception_args(self):
        message = "exception message"

        class TimeExecutionException(Exception):
            def __init__(self, msg, required):
                super(TimeExecutionException, self).__init__(msg)

        def exception_hook(exception, **kwargs):
            assert isinstance(exception, (TimeExecutionException,))
            return dict(exception_message=str(exception))

        def asserts(name, **data):
            assert data["exception_message"] == message

        @time_execution
        def go():
            raise TimeExecutionException(message, True)

        with settings(backends=[AssertBackend(asserts)], hooks=[exception_hook]):
            with pytest.raises(TimeExecutionException):
                go()

    def test_hook_func_args(self):
        param = "foo"

        @time_execution
        def go(param1):
            return "200 OK"

        def hook(response, exception, metric, func, func_args, func_kwargs):
            assert func_args[0] == param

        with settings(hooks=[hook]):
            go(param)

    def test_hook_func_kwargs(self):
        param = "foo"

        @time_execution
        def go(param1):
            return "200 OK"

        def hook(response, exception, metric, func, func_args, func_kwargs):
            assert func_kwargs["param1"] == param

        with settings(hooks=[hook]):
            go(param1=param)

    def test_generator_hook(self) -> None:
        is_started = False

        def generator_hook(func, func_args, func_kwargs) -> GeneratorHookReturnType:
            assert func_args == (42,)
            assert func_kwargs == {"bar": 100500}
            assert not is_started, "the decorated function should not run just yet"
            (response, _exception, _metrics) = yield
            assert is_started
            assert response == "response"
            return {"key": "value"}

        @time_execution(disable_default_hooks=True, extra_hooks=(generator_hook,))
        def go(foo: int, *, bar: int) -> str:
            nonlocal is_started
            is_started = True
            return "response"

        def asserts(_name, **data):
            assert data["key"] == "value"

        with settings(backends=[AssertBackend(asserts)]):
            assert go(42, bar=100500) == "response"

    def test_generator_hook_did_not_stop(self) -> None:
        def generator_hook(func, func_args, func_kwargs) -> GeneratorHookReturnType:
            yield
            yield  # this extra `yield` is incorrect
            return {}

        @time_execution(disable_default_hooks=True, extra_hooks=(generator_hook,))
        def go() -> None:
            return None

        with pytest.raises(RuntimeError, match="generator hook did not stop"):
            go()
