from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

import pytest

from cloudshell.logging.qs_logger import _LOGGER_CONTAINER, get_qs_logger
from cloudshell.logging.utils.decorators import command_logging
from cloudshell.logging.utils.venv import get_venv_name

logger = logging.getLogger(__name__)
venv_name = get_venv_name()


@pytest.fixture(autouse=True)
def clear_loggers():
    yield
    _LOGGER_CONTAINER.clear()
    logger = logging.getLogger("tests")
    logger.handlers.clear()


@command_logging
def command(error: bool):
    logger.info("Command")
    if error:
        raise Exception("Error")


def test_command_logging():
    os.environ["LOG_LEVEL"] = "DEBUG"

    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ["LOG_PATH"] = temp_dir

        _ = get_qs_logger(log_category="tests", log_group="group")

        command(error=False)

        folder_path = Path(temp_dir) / "group" / venv_name
        file_paths = list(folder_path.glob("QS*.log"))
        assert len(file_paths) == 1
        log_records = file_paths[0].read_text()

        assert 'Start command "command"' in log_records
        assert "Command" in log_records
        assert 'Command "command" finished successfully' in log_records


def test_command_logging_failed():
    os.environ["LOG_LEVEL"] = "DEBUG"

    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ["LOG_PATH"] = temp_dir

        _ = get_qs_logger(log_category="tests", log_group="group")

        with pytest.raises(Exception):
            command(error=True)

        folder_path = Path(temp_dir) / "group" / venv_name
        file_paths = list(folder_path.glob("QS*.log"))
        assert len(file_paths) == 1
        log_records = file_paths[0].read_text()

        assert 'Start command "command"' in log_records
        assert "Command" in log_records
        assert 'Command "command" finished unsuccessfully' in log_records
