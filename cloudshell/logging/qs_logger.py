from __future__ import annotations

import logging
import os
import re
import sys
import threading
import time
import traceback
from datetime import datetime
from functools import wraps
from logging.handlers import RotatingFileHandler
from pathlib import Path

from cloudshell.logging.context_filters import (
    FilterByContext,
    FilterOnlyWithoutContext,
    set_logger_context,
)
from cloudshell.logging.memory_handler import LimitedMemoryHandler
from cloudshell.logging.qs_config_parser import QSConfigParser
from cloudshell.logging.utils.log_exec_info import log_execution_info
from cloudshell.logging.utils.patch_logging_shutdown import patch_logging_shutdown
from cloudshell.logging.utils.venv import get_venv_name

# Logging Levels
LOG_LEVELS = {
    "INFO": logging.INFO,
    "WARN": logging.WARN,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
    "FATAL": logging.FATAL,
    "DEBUG": logging.DEBUG,
}

# default settings
DEFAULT_FORMAT = (
    "%(asctime)s [%(levelname)s]: "
    "%(threadName)s %(module)s - %(funcName)-20s %(message)s"
)
DEFAULT_TIME_FORMAT = "%Y%m%d%H%M%S"
DEFAULT_LEVEL = "INFO"
DEFAULT_PRIORITY = "ENV"
LOG_SECTION = "Logging"
WINDOWS_OS_FAMILY = "nt"

_LOGGER_CONTAINER = {}
_LOGGER_LOCK = threading.Lock()


def get_settings():
    """Read configuration settings from config or use DEFAULTS.

    :return: config obj
    """
    config = QSConfigParser().get_config(section=LOG_SECTION)

    priority = config.get("LOG_PRIORITY", DEFAULT_PRIORITY)
    if priority == "ENV" and os.getenv("LOG_LEVEL"):
        config["LOG_LEVEL"] = os.getenv("LOG_LEVEL")
    elif priority == "CONFIG":
        config["LOG_LEVEL"] = config.get("LOG_LEVEL", DEFAULT_LEVEL)
    else:
        config["LOG_LEVEL"] = DEFAULT_LEVEL

    config["LOG_FORMAT"] = (
        config.get("LOG_FORMAT") or config.get("FORMAT") or DEFAULT_FORMAT
    )
    config["TIME_FORMAT"] = config.get("TIME_FORMAT") or DEFAULT_TIME_FORMAT
    config["MEMORY_LOG_SIZE"] = int(
        os.getenv("QS_MEMORY_LOG_SIZE", config.get("MEMORY_LOG_SIZE", 500))
    )

    return config


def _set_log_level(logger, config):
    log_level = config.get("LOG_LEVEL", DEFAULT_LEVEL)

    for handler in logger.handlers:
        if not isinstance(handler, LimitedMemoryHandler):
            try:
                handler.setLevel(log_level)
            except ValueError:
                handler.setLevel(DEFAULT_LEVEL)


def _get_log_path_config(config):
    """Get log path based on the environment variable or Windows/Unix config setting.

    :param dict[str] config:
    :rtype: str
    """
    if "LOG_PATH" in os.environ:
        return os.environ["LOG_PATH"]

    if os.name == WINDOWS_OS_FAMILY:
        tpl = config.get("WINDOWS_LOG_PATH")
        if tpl:
            try:
                return tpl.format(**os.environ)
            except KeyError:
                print(  # noqa: T201
                    f"Environment variable is not defined in the template {tpl}"
                )
    else:
        return config.get("UNIX_LOG_PATH")


def _prepare_log_path(log_path, log_file_name):
    """Create logs directory if needed and return full path to the log file.

    :param str log_path:
    :param str log_file_name:
    :rtype: str
    """
    if log_path.startswith(".."):
        log_path = os.path.join(os.path.dirname(__file__), log_path)

    log_file = os.path.join(log_path, log_file_name)

    if os.path.isdir(log_path):
        if os.access(log_path, os.W_OK):
            return log_file
    else:
        try:
            os.makedirs(log_path)
            return log_file
        except Exception:
            pass


# return accessable log path or None
def get_accessible_log_path(reservation_id="Autoload", handler="default"):
    """Generate log path for the logger and verify that it's accessible.

     Using LOG_PATH/reservation_id/handler-%timestamp%.log

    :param reservation_id: part of log path
    :param handler: handler name for logger
    :return: generated log path
    """
    config = get_settings()
    time_format = config["TIME_FORMAT"] or DEFAULT_TIME_FORMAT
    log_file_name = f"{handler}--{datetime.now().strftime(time_format)}.log"

    log_path = _get_log_path_config(config)

    if log_path:
        shell_name = get_venv_name()
        log_path = os.path.join(log_path, reservation_id, shell_name)
        path = _prepare_log_path(log_path=log_path, log_file_name=log_file_name)
        if path:
            return path

    default_log_path = config.get("DEFAULT_LOG_PATH")

    if default_log_path:
        default_log_path = os.path.join(default_log_path, reservation_id)
        return _prepare_log_path(log_path=default_log_path, log_file_name=log_file_name)


def get_qs_logger(
    log_group: str = "Ungrouped",
    log_category: str = "cloudshell",
    log_file_prefix: str = "QS",
    exec_info: dict | None = None,
) -> logging.Logger:
    """Create cloudshell specific singleton logger.

    :param log_group: This folder will be grouped under this name.
    The default implementation of the group is a folder under the logs directory.
    According to the CloudShell logging standard pass the reservation id as this value
    when applicable, otherwise use the operation name (e.g 'Autoload').

    :param log_category: All messages to this logger will be prefixed by the
    category name. The category name should be the name of the shell/driver

    :param log_file_prefix: The log file generated by this logger will have this
    specified prefix. According to the logging standard the prefix should be the
    name of the resource the command is executing on. For environment commands
    use the command name.

    :param exec_info: dict with execution info {LOG_LEVEL: {KEY: VALUE}}
        VALUE can be a string or list of strings

    :return: the logger object
    """
    set_logger_context(folder_name=log_group, file_prefix=log_file_prefix)
    config = get_settings()
    _LOGGER_LOCK.acquire()
    try:
        if log_group in _LOGGER_CONTAINER:
            logger = _LOGGER_CONTAINER[log_group]
            # log level may change between executions
            _set_log_level(logger, config)
        else:
            logger = _create_logger(
                log_group, log_category, log_file_prefix, config=config
            )
            _LOGGER_CONTAINER[log_group] = logger
            # we have to set log level before logging exec info
            _set_log_level(logger, config)
            if exec_info:
                log_execution_info(logger, exec_info)
    finally:
        _LOGGER_LOCK.release()

    return logger


def _create_logger(log_group, log_category, log_file_prefix, config=None):
    """Create logging handler.

    :param log_group: This folder will be grouped under this name.
    The default implementation of the group is a folder under the logs directory.
    According to the CloudShell logging standard pass the reservation id as this value
    when applicable, otherwise use the operation name (e.g 'Autoload').
    :type log_group: str

    :param log_category: All messages to this logger will be prefixed by the
    category name. The category name should be the name of the shell/driver
    :type log_category: str

    :param log_file_prefix: The log file generated by this logger will have this
    specified prefix. According to the logging standard the prefix should be the name
    of the resource the command is executing on. For environment commands
    use the command name.
    :type log_file_prefix: str

    :return: the logger object
    :rtype: logging.Logger
    """
    config = config or get_settings()
    logger = logging.getLogger(log_category)
    logger.setLevel(logging.DEBUG)
    _add_handler_with_context(logger, config, log_file_prefix, log_group)
    _add_handler_without_context(logger, config)

    return logger


def _add_handler_with_context(logger, config, file_prefix, folder_name) -> None:
    filter_by_context = FilterByContext(
        logger.name,
        folder_name=folder_name,
        file_prefix=file_prefix,  # use original file prefix
    )
    log_file_prefix = re.sub(" ", "_", file_prefix)

    log_path = get_accessible_log_path(folder_name, log_file_prefix)
    if log_path:
        hdlr1 = logging.FileHandler(log_path, mode="a")
        hdlr2 = _add_memory_handler(log_path, config)
        hdlrs = (hdlr1, hdlr2)
    else:
        hdlrs = (logging.StreamHandler(sys.stdout),)

    for hdlr in hdlrs:
        hdlr.addFilter(filter_by_context)

        formatter = MultiLineFormatter(config["LOG_FORMAT"])
        hdlr.setFormatter(formatter)

        logger.addHandler(hdlr)


def _add_memory_handler(log_path: str, config):
    log_path = Path(log_path)
    folder_path = log_path.parent
    file_name = log_path.name.rstrip(".log") + "-debug.log"
    debug_log_path = folder_path / file_name

    target_hdlr = logging.FileHandler(debug_log_path, mode="a", delay=True)
    memory_hdlr = LimitedMemoryHandler(config["MEMORY_LOG_SIZE"], target_hdlr)
    patch_logging_shutdown()

    formatter = MultiLineFormatter(config["LOG_FORMAT"])
    target_hdlr.setFormatter(formatter)

    return memory_hdlr


def _add_handler_without_context(logger, config) -> None:
    log_path = _get_log_path_config(config)
    if not log_path:
        return  # we save missed logs only for file handlers

    missing_logs_name = "missed_logs.log"
    missing_logs_path = os.path.join(log_path, missing_logs_name)

    for h in logger.handlers:
        if isinstance(h, RotatingFileHandler):
            if h.baseFilename.endswith(missing_logs_name):
                break
    else:
        hdlr = RotatingFileHandler(
            missing_logs_path,
            mode="a",
            delay=True,
            maxBytes=10 * 1024 * 1024,
            backupCount=2,
        )
        formatter = MultiLineFormatter(config["LOG_FORMAT"])
        hdlr.setFormatter(formatter)
        filter_ = FilterOnlyWithoutContext(logger.name)
        hdlr.addFilter(filter_)
        logger.addHandler(hdlr)


def qs_time_this(func):
    """Decorator that reports the execution time."""  # noqa: D202

    @wraps(func)
    def wrapper(*args, **kwargs):
        _logger = get_qs_logger()
        start = time.time()
        _logger.info("%s started" % func.__name__)
        result = func(*args, **kwargs)
        end = time.time()
        _logger.info(f"{func.__name__} ended taking {str(end - start)}")
        return result

    return wrapper


def get_log_path(logger=logging.getLogger()):
    for hdlr in logger.handlers:
        if isinstance(hdlr, logging.FileHandler):
            return hdlr.baseFilename
    return None


def normalize_buffer(input_buffer):
    """Clear color from input_buffer and special characters.

    :param str input_buffer: input buffer string from device
    :return: str
    """
    # \033[1;32;40m
    # \033[ - Escape code
    # 1     - style
    # 32    - text color
    # 40    - Background colour
    color_pattern = re.compile(
        r"\[(\d+;){0,2}?\d+m|\b|" + chr(27)
    )  # 27 - ESC character

    result_buffer = ""

    if not isinstance(input_buffer, str):
        input_buffer = str(input_buffer)

    match_iter = color_pattern.finditer(input_buffer)

    current_index = 0
    for match_color in match_iter:
        match_range = match_color.span()
        result_buffer += input_buffer[current_index : match_range[0]]
        current_index = match_range[1]

    result_buffer += input_buffer[current_index:]

    result_buffer = result_buffer.replace("\r\n", "\n")

    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]", "", result_buffer)


class MultiLineFormatter(logging.Formatter):
    """Log Formatter, Append log header to each line."""

    MAX_SPLIT = 1

    def format(self, record):  # noqa: A003
        """Formatting for one or multi-line message.

        :param record:
        :return:
        """
        s = ""

        if record.msg == "":
            return s

        try:
            record.msg = normalize_buffer(record.msg)
            s = logging.Formatter.format(self, record)
            header, footer = s.rsplit(record.message, self.MAX_SPLIT)
            s = s.replace("\n", "\n" + header)
        except Exception as e:
            print(traceback.format_exc())  # noqa: T201
            print("logger.format: Unexpected error: " + str(e))  # noqa: T201
            print(f"record = {traceback.format_exc()}<<<")  # noqa: T201
        return s


class Loggable:
    """Interface for Instances which uses Logging."""

    LOG_LEVEL = LOG_LEVELS["WARN"]  # Default Level that will be reported
    LOG_INFO = LOG_LEVELS["INFO"]
    LOG_WARN = LOG_LEVELS["WARN"]
    LOG_ERROR = LOG_LEVELS["ERROR"]
    LOG_CRITICAL = LOG_LEVELS["CRITICAL"]
    LOG_FATAL = LOG_LEVELS["FATAL"]
    LOG_DEBUG = LOG_LEVELS["DEBUG"]

    def setup_logger(self):
        """Setup local logger instance."""
        self.logger = get_qs_logger(self.__class__.__name__)
        self.logger.setLevel(self.LOG_LEVEL)
        # Logging methods aliases
        self.logDebug = self.logger.debug
        self.logInfo = self.logger.info
        self.logWarn = self.logger.warn
        self.logError = self.logger.error
