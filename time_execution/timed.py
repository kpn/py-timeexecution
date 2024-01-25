from __future__ import annotations

from collections.abc import Iterable
from contextlib import AbstractContextManager
from inspect import isgenerator, isgeneratorfunction
from socket import gethostname
from timeit import default_timer
from types import TracebackType
from typing import Any, Callable, Dict, Optional, Tuple, Type, cast

from time_execution import GeneratorHook, GeneratorHookReturnType, Hook, settings, write_metric

SHORT_HOSTNAME = gethostname()


class Timed(AbstractContextManager):
    """
    Both the sync and async decorators require the same logic around the wrapped function.
    This context manager encapsulates the shared behaviour to avoid duplicating the code.
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

    def __enter__(self) -> Timed:
        self._start_time = default_timer()
        for hook in self._hooks:
            if isgenerator(hook):
                hook.send(None)  # start a generator hook
        return self

    def __exit__(
        self,
        __exc_type: Optional[Type[BaseException]],
        __exc_val: Optional[BaseException],
        __exc_tb: Optional[TracebackType],
    ) -> None:
        duration_millis = round(default_timer() - self._start_time, 3) * 1000.0

        metric = {settings.duration_field: duration_millis, "hostname": SHORT_HOSTNAME, "name": self._fqn}

        origin = getattr(settings, "origin", None)
        if origin:
            metric["origin"] = origin

        # Apply the registered hooks, and collect the metadata they might
        # return to be stored with the metrics.
        metadata = self._apply_hooks(
            response=self.result,
            exception=__exc_val,
            metric=metric,
        )

        metric.update(metadata)
        write_metric(**metric)  # type: ignore[arg-type]

    def _apply_hooks(self, response, exception, metric) -> Dict:
        metadata: Dict[str, Any] = dict()
        for hook in self._hooks:
            if not isgenerator(hook):
                # Simple exit hook, call it directly.
                hook_result = cast(Hook, hook)(
                    response=response,
                    exception=exception,
                    metric=metric,
                    func=self._wrapped,
                    func_args=self._call_args,
                    func_kwargs=self._call_kwargs,
                )
            else:
                # Generator hook: send the results and obtain custom metadata.
                try:
                    hook.send((response, exception, metric))
                except StopIteration as e:
                    hook_result = e.value
                else:
                    raise RuntimeError("generator hook did not stop")
            if hook_result:
                metadata.update(hook_result)
        return metadata
