from __future__ import annotations

import logging
from logging import LogRecord
from logging.handlers import BufferingHandler

import pytest

from cloudshell.logging.utils.log_exec_info import log_execution_info


@pytest.fixture()
def handler():
    return BufferingHandler(100)


@pytest.fixture()
def logger(handler):
    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger


def test_log_execution_info(logger, handler):
    info = {
        "INFO": {
            "Reservation ID": "reservation id",
            "User": "user",
            "Environment Name": "environment name",
        },
        "DEBUG": {
            "Installed packages": [
                "attrs == 19.3.0",
                "cloudshell-automation-api == 2021.1.0",
            ],
        },
    }

    log_execution_info(logger, info)

    assert len(handler.buffer) == 6  # 4 header + 4 records + footer

    # first record is execution info header
    first_log_record: LogRecord = handler.buffer[1]
    assert first_log_record.levelname == "INFO"
    assert first_log_record.msg == "Reservation ID      : reservation id"

    second_log_record: LogRecord = handler.buffer[2]
    assert second_log_record.levelname == "INFO"
    assert second_log_record.msg == "User                : user"

    third_log_record: LogRecord = handler.buffer[3]
    assert third_log_record.levelname == "INFO"
    assert third_log_record.msg == "Environment Name    : environment name"

    fourth_log_record: LogRecord = handler.buffer[4]
    assert fourth_log_record.levelname == "DEBUG"
    expected_msg = (
        "Installed packages  : \n"
        "\t\tattrs == 19.3.0\n"
        "\t\tcloudshell-automation-api == 2021.1.0"
    )
    assert fourth_log_record.msg == expected_msg
