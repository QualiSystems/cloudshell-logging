from __future__ import annotations

import logging
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor, wait
from contextvars import copy_context
from logging.handlers import RotatingFileHandler

import pytest

from .package_file import do_smth

from cloudshell.logging.context_filters import (
    pass_log_context,
    set_logger_context_from_parent,
)
from cloudshell.logging.qs_logger import get_qs_logger
from cloudshell.logging.utils.venv import get_venv_name

env_name = get_venv_name()


def command(folder_name: str, file_prefix: str) -> None:
    # create logger in thread
    _ = get_qs_logger(
        log_category="tests", log_file_prefix=file_prefix, log_group=folder_name
    )

    do_smth(folder_name)


def command_with_thread_not_passed_context(folder_name: str, file_prefix: str) -> None:
    # create logger in thread
    _ = get_qs_logger(
        log_category="tests", log_file_prefix=file_prefix, log_group=folder_name
    )

    threading.Thread(target=do_smth, args=(folder_name,)).start()


def command_with_thread_executor_passed_context(
    folder_name: str, file_prefix: str
) -> None:
    # create logger in thread
    _ = get_qs_logger(
        log_category="tests", log_file_prefix=file_prefix, log_group=folder_name
    )

    with ThreadPoolExecutor(initializer=pass_log_context()) as executor:
        futures = [executor.submit(do_smth, folder_name)]
        wait(futures)


def command_with_simple_thread_passed_context(
    folder_name: str, file_prefix: str
) -> None:
    # create logger in thread
    _ = get_qs_logger(
        log_category="tests", log_file_prefix=file_prefix, log_group=folder_name
    )

    def wrapper():
        parent_context = copy_context()

        def wrapped(*args, **kwargs):
            set_logger_context_from_parent(parent_context)
            do_smth(*args, **kwargs)

        return wrapped

    t = threading.Thread(target=wrapper(), args=(folder_name,))
    t.start()
    t.join()


def command_with_own_thread_class_passed_context(
    folder_name: str, file_prefix: str
) -> None:
    # create logger in thread
    _ = get_qs_logger(
        log_category="tests", log_file_prefix=file_prefix, log_group=folder_name
    )

    class MyThread(threading.Thread):
        def __init__(self, parent_context, folder_name):
            super().__init__()
            self.parent_context = parent_context
            self.folder_name = folder_name

        def run(self):
            set_logger_context_from_parent(self.parent_context)
            do_smth(folder_name)

    t = MyThread(copy_context(), folder_name)
    t.start()
    t.join()


@pytest.mark.parametrize(
    "command_to_execute",
    [
        command,
        command_with_thread_executor_passed_context,
        command_with_simple_thread_passed_context,
        command_with_own_thread_class_passed_context,
    ],
)
def test_getting_logger(command_to_execute, tmp_path):
    reservation_ids = list(map(str, range(10)))
    file_prefix = "resource name"
    os.environ["LOG_PATH"] = str(tmp_path)

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(command_to_execute, rid, file_prefix)
            for rid in reservation_ids
        ]
        wait(futures)

    logger = logging.getLogger("tests")
    for h in logger.handlers:
        if getattr(h, "flushOnClose", True):
            h.flush()
    # file name would be changed, but we use original in context vars
    updated_file_prefix = file_prefix.replace(" ", "_")
    for rid in reservation_ids:
        folder_path = tmp_path / rid / env_name
        file_paths = list(folder_path.glob(f"{updated_file_prefix}*.log"))
        assert len(file_paths) == 1
        log_records = file_paths[0].read_text()

        assert len(re.findall(r"do smth with", log_records)) == 1
        assert f"do smth with {rid}" in log_records

    missed_logs_path = tmp_path / "missed_logs.log"
    assert not missed_logs_path.exists()


def test_log_records_without_context(tmp_path):
    folder_name = "1"
    file_prefix = "resource_name"
    os.environ["LOG_PATH"] = str(tmp_path)

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(command_with_thread_not_passed_context, "1", file_prefix)
        ]
        wait(futures)

    logger = logging.getLogger("tests")
    for h in logger.handlers:
        if getattr(h, "flushOnClose", True):
            h.flush()

    # standard logs don't have our log records
    folder_path = tmp_path / folder_name / env_name
    file_paths = list(folder_path.glob(f"{file_prefix}*.log"))
    assert len(file_paths) == 1  # exec info
    log_records = file_paths[0].read_text()
    assert "do smth with" not in log_records

    # but missed logs have log records
    missed_logs_path = tmp_path / "missed_logs.log"
    for h in logger.handlers:
        if isinstance(h, RotatingFileHandler):
            assert h.baseFilename == str(missed_logs_path)
            break
    else:
        assert False, "FileHandler not found"

    assert missed_logs_path.exists()
    log_records = missed_logs_path.read_text()
    assert len(re.findall(r"do smth with", log_records)) == 1
    assert f"do smth with {folder_name}" in log_records
