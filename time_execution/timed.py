from __future__ import annotations

from collections.abc import Iterable
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from inspect import iscoroutinefunction, isgenerator, isgeneratorfunction
from socket import gethostname
from timeit import default_timer
from types import TracebackType
from typing import Any, Callable, Dict, Optional, Tuple, Type, cast

from time_execution import GeneratorHook, GeneratorHookReturnType, Hook, settings, write_metric

SHORT_HOSTNAME = gethostname()


class Base:
    """
    Base class for context managers encapsulates the shared behaviour to avoid duplicating the code.
    """

    __slots__ = (
        "result",
        "_wrapped",
        "_fqn",
        "_hooks",
        "_call_args",
        "_call_kwargs",
        "_start_time",
    )

    def __init__(
        self,
        *,
        wrapped: Callable[..., Any],
        fqn: str,
        call_args: Tuple[Any, ...],
        call_kwargs: Dict[str, Any],
        extra_hooks: Optional[Iterable[Hook | GeneratorHook]] = None,
        disable_default_hooks: bool = False,
    ) -> None:
        self.result: Optional[Any] = None
        self._wrapped = wrapped
        self._fqn = fqn
        self._call_args = call_args
        self._call_kwargs = call_kwargs

        hooks = extra_hooks or ()
        if not disable_default_hooks:
            hooks = (*settings.hooks, *hooks)

        self._hooks = tuple(
            (
                cast(Hook, hook)
                if not isgeneratorfunction(hook)  # simple hook, we'll call it in the exit
                # For a generator hook, call it. We'll start in the entrance.
                else cast(GeneratorHookReturnType, hook(func=wrapped, func_args=call_args, func_kwargs=call_kwargs))
            )
            for hook in hooks
        )

    def enter(self) -> Any:
        self._start_time = default_timer()
        for hook in self._hooks:
            if isgenerator(hook):
                hook.send(None)  # start a generator hook
        return self

    def get_metric(self) -> Dict[str, Any]:
        duration_millis = round(default_timer() - self._start_time, 3) * 1000.0

        metric = {settings.duration_field: duration_millis, "hostname": SHORT_HOSTNAME, "name": self._fqn}

        origin = getattr(settings, "origin", None)
        if origin:
            metric["origin"] = origin

        return metric

    def apply_hook(
        self,
        hook: Any,
        exception: Optional[BaseException],
        metric: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> None:
        if not isgenerator(hook):
            hook_result = cast(Hook, hook)(
                response=self.result,
                exception=exception,
                metric=metric,
                func=self._wrapped,
                func_args=self._call_args,
                func_kwargs=self._call_kwargs,
            )
        else:
            # Generator hook: send the results and obtain custom metadata.
            try:
                hook.send((self.result, exception, metric))
            except StopIteration as e:
                hook_result = e.value
            else:
                raise RuntimeError("generator hook did not stop")
        if hook_result:
            metadata.update(hook_result)


class Timed(AbstractContextManager, Base):

    def __enter__(self) -> Timed:
        return self.enter()

    def __exit__(
        self,
        __exc_type: Optional[Type[BaseException]],
        __exc_val: Optional[BaseException],
        __exc_tb: Optional[TracebackType],
    ) -> None:

        metadata: Dict[str, Any] = dict()
        metric: Dict[str, Any] = self.get_metric()

        for hook in self._hooks:
            self.apply_hook(hook=hook, exception=__exc_val, metric=metric, metadata=metadata)

        metric.update(metadata)
        write_metric(**metric)  # type: ignore[arg-type]


class TimedAsync(AbstractAsyncContextManager, Base):

    async def __aenter__(self) -> Timed:
        return self.enter()

    async def __aexit__(
        self,
        __exc_type: Optional[Type[BaseException]],
        __exc_val: Optional[BaseException],
        __exc_tb: Optional[TracebackType],
    ) -> None:

        metadata: Dict[str, Any] = dict()
        metric: Dict[str, Any] = self.get_metric()

        for hook in self._hooks:
            await self._apply_hook(hook=hook, exception=__exc_val, metric=metric, metadata=metadata)

        metric.update(metadata)
        write_metric(**metric)  # type: ignore[arg-type]

    async def _apply_hook(
        self,
        hook: Any,
        exception: Optional[BaseException],
        metric: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> None:
        if iscoroutinefunction(hook):
            hook_result = await hook(
                response=self.result,
                exception=exception,
                metric=metric,
                func=self._wrapped,
                func_args=self._call_args,
                func_kwargs=self._call_kwargs,
            )
            metadata.update(hook_result)
        else:
            self.apply_hook(hook=hook, exception=exception, metric=metric, metadata=metadata)
