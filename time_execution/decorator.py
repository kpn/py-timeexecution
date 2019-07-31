"""
Time Execution decorator
"""
import socket
import time
import warnings

import six
from fqn_decorators import Decorator
from pkgsettings import Settings

from .constants import PY_35_GT
from .deprecation import HookDeprecatedWarning

warnings.simplefilter('once', HookDeprecatedWarning)

SHORT_HOSTNAME = socket.gethostname()

settings = Settings()
settings.configure(backends=[], hooks=[], duration_field='value')


def write_metric(name, **metric):
    for backend in settings.backends:
        backend.write(name, **metric)


def _apply_hooks(hooks, response, exception, metric, func, func_args, func_kwargs):
    metadata = dict()
    for hook in hooks:
        # backward compatibility with old hooks
        try:
            hook_result = hook(
                response=response,
                exception=exception,
                metric=metric,
                func=func,
                func_args=func_args,
                func_kwargs=func_kwargs,
            )
        except TypeError:
            warnings.warn(
                "Hook %s is outdated. Update interface by adding one more argument `func` in it." % hook.__name__,
                HookDeprecatedWarning,
            )
            hook_result = hook(
                response=response, exception=exception, metric=metric, func_args=func_args, func_kwargs=func_kwargs
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

        metric = {'name': self.fqn, settings.duration_field: duration, 'hostname': SHORT_HOSTNAME}

        origin = getattr(settings, 'origin', None)
        if origin:
            metric['origin'] = origin

        hooks = self.params.get('extra_hooks', [])
        disable_default_hooks = self.params.get('disable_default_hooks', False)

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
        if self.exc_info:
            try:
                six.reraise(*self.exc_info)
            except Exception as e:
                return e


if PY_35_GT:
    from fqn_decorators.asynchronous import AsyncDecorator  # isort:skip

    class time_execution_async(AsyncDecorator, time_execution):
        pass
