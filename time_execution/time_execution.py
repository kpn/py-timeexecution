"""
Time Execution decorator
"""
import functools
import socket
import sys
import time


class Settings(object):
    """
    Settings class that will be used by the time_execution decorator

    Attributes:
        backends (list): List of backends
        hooks (list): List of hooks
    """
    def __init__(self, backends=None, hooks=[]):
        """
        Args:
            backends (Optional[list]): List of backends
            hooks (Optional[list]): List of hooks
        """
        self.backends = backends or []
        self.hooks = hooks or []


settings = Settings()


def configure(**kwargs):
    """
    Configure the time_executions package with a new settings object.

    Args:
        backends (Optional[list]): List of backends
        hooks (Optional[list]): List of hooks

    """
    global settings
    settings = Settings(**kwargs)


SHORT_HOSTNAME = socket.gethostname()


def write_metric(name, **metric):
    for backend in settings.backends:
        backend.write(name, **metric)


def _get_qualified_name(func):
    """
    For python 3 we should use __qualname__ but its not available in python 2
    so in order to be consistent until we upgrade we keep of basic
    """
    path = [func.__module__]
    if sys.version_info[0] > 2:
        qualname = getattr(func, '__qualname__', None)
        path.append(qualname.replace('<locals>.', ''))
    else:
        im_class = getattr(func, 'im_class', None)
        path.append(getattr(im_class, '__name__', None))
        path.append(func.__name__)
    return '.'.join(filter(None, path))


def _apply_hooks(**kwargs):
    metadata = dict()
    for hook in settings.hooks:
        hook_result = hook(**kwargs)
        if hook_result:
            metadata.update(hook_result)
    return metadata


class time_execution(object):
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.fqn = _get_qualified_name(self.func)
        functools.update_wrapper(self, func)

    def __get__(self, obj, type=None):
        return self.__class__(self.func.__get__(obj, type))

    def __call__(self, *args, **kwargs):
        start_time = time.time()
        response = None
        exception = None
        try:
            response = self.func(*args, **kwargs)
        except Exception as e:
            exception = e
            raise
        finally:

            duration = round(time.time() - start_time, 3) * 1000
            fqn = _get_qualified_name(self.func)

            metric = dict(
                name=fqn,
                duration=duration,
                hostname=SHORT_HOSTNAME
            )

            # Apply the registered hooks, and collect the metadata they might
            # return to be stored with the metrics
            metadata = _apply_hooks(
                response=response,
                exception=exception,
                metric=metric
            )

            metric.update(metadata)
            write_metric(**metric)

        return response
