from time_execution import time_execution


@time_execution
def go(*args, **kwargs):
    return True


@time_execution
class Dummy(object):
    @time_execution
    def go(self, *args, **kwargs):
        pass
