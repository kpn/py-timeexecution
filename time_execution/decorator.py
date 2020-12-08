"""
Time Execution decorator
"""
import socket
import time

from fqn_decorators import Decorator
from fqn_decorators.asynchronous import AsyncDecorator
from pkgsettings import Settings

SHORT_HOSTNAME = socket.gethostname()

settings = Settings()
settings.configure(backends=[], hooks=[], duration_field="value")


def write_metric(name, **metric):
    for backend in settings.backends:
        backend.write(name, **metric)


def _apply_hooks(hooks, response, exception, metric, func, func_args, func_kwargs):
    metadata = dict()
    for hook in hooks:
        hook_result = hook(
            response=response,
            exception=exception,
            metric=metric,
            func=func,
            func_args=func_args,
            func_kwargs=func_kwargs,
        )

        if hook_result:
            metadata.update(hook_result)
    return metadata


class time_execution(Decorator):
    def __init__(self, func=None, **params):
        self.start_time = None
        super(time_execution, self).__init__(func, **params)

    def before(self):
        self.start_time = time.time()

    def after(self):
        duration = round(time.time() - self.start_time, 3) * 1000

        metric = {"name": self.fqn, settings.duration_field: duration, "hostname": SHORT_HOSTNAME}

        origin = getattr(settings, "origin", None)
        if origin:
            metric["origin"] = origin

        hooks = self.params.get("extra_hooks", [])
        disable_default_hooks = self.params.get("disable_default_hooks", False)

        if not disable_default_hooks:
            hooks = settings.hooks + hooks

        # Apply the registered hooks, and collect the metadata they might
        # return to be stored with the metrics
        metadata = _apply_hooks(
            hooks=hooks,
            response=self.result,
            exception=self.get_exception(),
            metric=metric,
            func=self.func,
            func_args=self.args,
            func_kwargs=self.kwargs,
        )

        metric.update(metadata)
        write_metric(**metric)

    def get_exception(self):
        """Retrieve the exception"""
        if self.exc_info is None:
            return

        exc_type, exc_value, exc_tb = self.exc_info
        if exc_value is None:
            exc_value = exc_type()
        if exc_value.__traceback__ is not exc_tb:
            return exc_value.with_traceback(exc_tb)
        return exc_value


class time_execution_async(AsyncDecorator, time_execution):
    pass
