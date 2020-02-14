import os
import sys
from logging import FileHandler

from cloudshell.logging.interprocess_logger import MultiProcessingLog

if sys.version_info >= (3, 0):
    from functools import lru_cache
else:
    from functools32 import lru_cache


class LoggerOperationsException(Exception):
    pass


class NoFileHandler(LoggerOperationsException):
    pass


class LoggerOperations(object):
    class lock_handler(object):
        """Used to lock/unlock handler."""

        def __init__(self, logger):
            self._logger = logger

        def __enter__(self):
            for hdlr in self._logger.handlers:
                hdlr.acquire()
                if isinstance(hdlr, MultiProcessingLog):
                    hdlr.flush()
            return self._logger

        def __exit__(self, exc_type, exc_val, exc_tb):
            for hdlr in self._logger.handlers:
                hdlr.release()

    def __init__(self, logger):
        self._logger = logger

    def get_log_file_path(self):
        return self._get_file_handler().baseFilename

    @lru_cache()
    def _get_file_handler(self):
        for hdlr in self._logger.handlers:
            if isinstance(hdlr, FileHandler):
                return hdlr
            elif isinstance(hdlr, MultiProcessingLog):
                return hdlr.handler
        raise NoFileHandler("FileHandler is not defined")

    def move_to_file(self, new_file_path):
        """
        Change handler file.

        Move existing data from current file to the new file,
        switch handler to new file, remove unused file.

        Args:
            :param str new_file_path:
        """
        with self.lock_handler(self._logger):
            handler = self._get_file_handler()

            cur_file_path = handler.baseFilename
            if cur_file_path == new_file_path:
                return

            if not os.access(cur_file_path, os.R_OK):
                raise LoggerOperationsException(
                    "Cannot read cur logfile:" " {}".format(cur_file_path)
                )

            if not (
                os.path.exists(new_file_path) and os.access(new_file_path, os.W_OK)
            ) and not (
                os.path.exists(os.path.dirname(new_file_path))
                and os.access(os.path.dirname(new_file_path), os.W_OK)
            ):
                raise LoggerOperationsException(
                    "Cannot write to new logfile:" " {}".format(new_file_path)
                )
            if handler.stream:
                handler.stream.flush()
                handler.stream.close()
                handler.stream = None
            with open(cur_file_path, "rb") as c_f, open(new_file_path, "ab") as n_f:
                n_f.write(c_f.read())

            os.remove(cur_file_path)
            handler.baseFilename = new_file_path

    def rename_log_file(self, new_name):
        new_file_path = os.path.join(
            os.path.dirname(self.get_log_file_path()), new_name
        )
        self.move_to_file(new_file_path)
