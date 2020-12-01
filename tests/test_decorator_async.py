import asyncio
from unittest.mock import Mock

import pytest

from time_execution import time_execution_async


@pytest.fixture
def patch_backend(monkeypatch):
    m = Mock()
    monkeypatch.setattr("time_execution.decorator.write_metric", m)
    return m


@time_execution_async
async def go_async(arg=None):
    await asyncio.sleep(0.01)
    return arg


def dummy_hook(*args, **kwargs):
    return {"dummy_hook_called": True}


@time_execution_async(extra_hooks=[dummy_hook])
async def go_async_with_hook(arg=None):
    await asyncio.sleep(0.01)
    return arg


class TestTimeExecutionAsync:
    pytestmark = pytest.mark.asyncio

    async def test_plain(self, patch_backend):
        count = 4

        for i in range(count):
            await go_async()

        assert patch_backend.call_count == count
        call_args = patch_backend.call_args[1]
        assert call_args["name"] == "tests.test_decorator_async.go_async"
        assert call_args["value"] >= 10  # in ms

    async def test_with_arguments(self, patch_backend):
        res = await go_async("ok")

        assert res == "ok"
        assert patch_backend.call_count == 1
        call_args = patch_backend.call_args[1]
        assert call_args["name"] == "tests.test_decorator_async.go_async"
        assert call_args["value"] >= 10  # in ms

    async def test_plain_with_parametrized_decorator(self, patch_backend):
        count = 4

        for i in range(count):
            await go_async_with_hook()

        assert patch_backend.call_count == count
        call_args = patch_backend.call_args[1]
        assert call_args["name"] == "tests.test_decorator_async.go_async_with_hook"
        assert call_args["value"] >= 10  # in ms
        assert call_args["dummy_hook_called"] is True
