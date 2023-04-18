from __future__ import annotations

import atexit
import logging


def shutdown(handlerList=logging._handlerList):
    for wr in reversed(handlerList[:]):
        try:
            h = wr()
            if h:
                try:
                    h.acquire()
                    # this is only the change from the original
                    # in Python 3.12 it should work like this:
                    if getattr(h, "flushOnClose", True):
                        h.flush()
                    h.close()
                except (OSError, ValueError):
                    pass
                finally:
                    h.release()
        except:  # noqa: E722
            if logging.raiseExceptions:
                raise


def patch_logging_shutdown():
    if not hasattr(logging.shutdown, "patched"):
        atexit.unregister(logging.shutdown)
        atexit.register(shutdown)
        logging.shutdown.patched = True
