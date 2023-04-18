from __future__ import annotations

import logging

import pytest

from cloudshell.logging.qs_logger import _LOGGER_CONTAINER


@pytest.fixture(autouse=True)
def clear_loggers():
    yield
    _LOGGER_CONTAINER.clear()
    logger = logging.getLogger("tests")
    logger.handlers.clear()
