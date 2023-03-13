"""
Time Execution decorator
"""
from asyncio import iscoroutinefunction
from functools import wraps
from typing import Any, Callable, List, Optional, TypeVar, cast

import fqn_decorators
from pkgsettings import Settings
from typing_extensions import overload

_F = TypeVar("_F", bound=Callable[..., Any])

settings = Settings()
settings.configure(backends=[], hooks=[], duration_field="value")


def write_metric(name: str, **metric: Any) -> None:
    for backend in settings.backends:
        backend.write(name, **metric)


@overload
def time_execution(__wrapped: _F) -> _F:
    """First-order (non-parametrized) decorator with the default FQN getter and hooks by default."""


@overload
def time_execution(
    *,
    get_fqn: Callable[[Any], str] = fqn_decorators.get_fqn,
    extra_hooks: Optional[List] = None,
    disable_default_hooks: bool = False,
) -> Callable[[_F], _F]:
    """
    Second-order (parametrized) decorator.

    Args:
        get_fqn: custom FQN getter (uses `fqn-decorators` by default)
        extra_hooks: additional hooks (next to defined in the settings)
        disable_default_hooks: if `True`, disable the hooks set by the settings
    """


def time_execution(__wrapped=None, get_fqn: Callable[[Any], str] = fqn_decorators.get_fqn, **kwargs):
    from time_execution.timed import Timed  # work around the circular dependency

    def wrap(__wrapped: _F) -> _F:
        fqn = get_fqn(__wrapped)

        if not iscoroutinefunction(__wrapped):

            @wraps(__wrapped)
            def wrapper(*call_args, **call_kwargs):
                with Timed(wrapped=__wrapped, call_args=call_args, call_kwargs=call_kwargs, fqn=fqn, **kwargs) as timed:
                    timed.result = __wrapped(*call_args, **call_kwargs)
                    return timed.result

        else:

            @wraps(__wrapped)
            async def wrapper(*call_args, **call_kwargs):
                with Timed(wrapped=__wrapped, call_args=call_args, call_kwargs=call_kwargs, fqn=fqn, **kwargs) as timed:
                    timed.result = await __wrapped(*call_args, **call_kwargs)
                    return timed.result

        # Backwards compatibility with `Decorator`.
        wrapper.fqn = fqn  # type: ignore[attr-defined]
        wrapper.get_fqn = lambda: wrapper.fqn  # type: ignore[attr-defined]
        return cast(_F, wrapper)

    return wrap(__wrapped) if __wrapped is not None else wrap


# `time_execution` supports async out of the box.
time_execution_async = time_execution
