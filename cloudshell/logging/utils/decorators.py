from functools import wraps


def command_logging(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        func_name = func.__name__

        self._logger.debu('Start command "{}"'.format(func_name))
        finishing_msg = 'Command "{}" finished {}'
        try:
            result = func(self, *args, **kwargs)
        except Exception:
            self._logger.info(finishing_msg.format(func_name, 'unsuccessfully'))
            raise
        else:
            self._logger.info(finishing_msg.format(func_name, 'successfully'))

        return result

    return wrapped
