from __future__ import annotations

import logging
from functools import wraps


def command_logging(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        func_name = func.__name__
        module_name = func.__module__
        logger = logging.getLogger(module_name)

        logger.debug(f'Start command "{func_name}"')
        finishing_msg = f'Command "{func_name}" finished {{}}'
        try:
            result = func(*args, **kwargs)
        except Exception:
            logger.debug(finishing_msg.format("unsuccessfully"))
            raise
        else:
            logger.debug(finishing_msg.format("successfully"))

        return result

    return wrapped
