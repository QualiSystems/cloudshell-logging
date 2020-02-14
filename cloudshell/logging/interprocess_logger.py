import logging
import multiprocessing
import sys
import threading
import time
import traceback
from logging.handlers import RotatingFileHandler

if sys.version_info >= (3, 0):
    from queue import Empty
else:
    from Queue import Empty


class MultiProcessingLogException(Exception):
    pass


class MultiProcessingLog(logging.Handler):
    def __init__(self, name, mode="a", maxsize=0, rotate=0):
        logging.Handler.__init__(self)

        self.handler = RotatingFileHandler(name, mode, maxsize, rotate)
        self.queue = multiprocessing.Queue(-1)
        self._is_closed = False
        self._receive_thread = threading.Thread(target=self.receive)
        self._receive_thread.daemon = True
        self._receive_thread.start()

    def setFormatter(self, fmt):
        logging.Handler.setFormatter(self, fmt)
        self.handler.setFormatter(fmt)

    def receive(self):
        while not self._is_closed or not self.queue.empty():
            try:
                record = self.queue.get(block=True, timeout=0.1)
                self.handler.emit(record)
            except Empty:
                continue
            except (KeyboardInterrupt, SystemExit):
                raise
            except EOFError:
                break
            except Exception:
                traceback.print_exc(file=sys.stderr)
        self.queue.close()
        self.queue.join_thread()

    def send(self, s):
        if not self._is_closed:
            self.queue.put(s)
        else:
            raise MultiProcessingLogException("Cannot send record, when handler closed")

    def _format_record(self, record):
        # ensure that exc_info and args
        # have been stringified.  Removes any chance of
        # unpickleable things inside and possibly reduces
        # message size sent over the pipe
        if record.args:
            record.msg = record.msg % record.args
            record.args = None
        if record.exc_info:
            self.format(record)
            record.exc_info = None

        return record

    def emit(self, record):
        try:
            s = self._format_record(record)
            self.send(s)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)

    def flush(self):
        while not self.queue.empty():
            time.sleep(0.1)

    def close(self):
        self._is_closed = True
        self._receive_thread.join(5)
        self.handler.close()
        logging.Handler.close(self)
