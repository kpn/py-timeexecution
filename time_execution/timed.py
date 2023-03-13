from __future__ import annotations

from contextlib import AbstractContextManager
from socket import gethostname
from timeit import default_timer
from types import TracebackType
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from time_execution import settings, write_metric

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
        "_extra_hooks",
        "_disable_default_hooks",
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
        extra_hooks: Optional[List] = None,
        disable_default_hooks: bool = False,
    ) -> None:
        self.result: Optional[Any] = None
        self._wrapped = wrapped
        self._fqn = fqn
        self._extra_hooks = extra_hooks
        self._disable_default_hooks = disable_default_hooks
        self._call_args = call_args
        self._call_kwargs = call_kwargs

    def __enter__(self) -> Timed:
        self._start_time = default_timer()
        return self

    def __exit__(
        self,
        __exc_type: Optional[Type[BaseException]],
        __exc_val: Optional[BaseException],
        __exc_tb: Optional[TracebackType],
    ) -> None:
        duration_millis = round(default_timer() - self._start_time, 3) * 1000.0

        metric = {settings.duration_field: duration_millis, "hostname": SHORT_HOSTNAME}

        origin = getattr(settings, "origin", None)
        if origin:
            metric["origin"] = origin

        hooks = self._extra_hooks or []
        if not self._disable_default_hooks:
            hooks = settings.hooks + hooks

        # Apply the registered hooks, and collect the metadata they might
        # return to be stored with the metrics.
        metadata = self._apply_hooks(hooks=hooks, response=self.result, exception=__exc_val, metric=metric)

        metric.update(metadata)
        write_metric(name=self._fqn, **metric)

    def _apply_hooks(self, hooks, response, exception, metric) -> Dict:
        metadata = dict()
        for hook in hooks:
            hook_result = hook(
                response=response,
                exception=exception,
                metric=metric,
                func=self._wrapped,
                func_args=self._call_args,
                func_kwargs=self._call_kwargs,
            )
            if hook_result:
                metadata.update(hook_result)
        return metadata
