from __future__ import annotations

from logging import DEBUG, NullHandler, getLogger
from logging.handlers import BufferingHandler

import pytest

from cloudshell.logging.memory_handler import LimitedMemoryHandler


@pytest.fixture()
def logger():
    logger = getLogger(__name__)
    logger.setLevel(DEBUG)
    return logger


@pytest.fixture()
def handler():
    return LimitedMemoryHandler(max_len=2, target=NullHandler())


def test_limited_memory_handler_keeps_only_last_n_records(logger, handler):
    logger.addHandler(handler)

    logger.info("1")
    logger.info("2")
    logger.info("3")

    assert len(handler.buffer) == 2
    assert handler.buffer[0].msg == "2"
    assert handler.buffer[1].msg == "3"


def test_limited_memory_handler_change_max_len(logger, handler):
    logger.addHandler(handler)

    logger.info("1")
    logger.info("2")

    handler.change_max_len(1)

    assert len(handler.buffer) == 1
    assert handler.buffer[0].msg == "2"


def test_limited_memory_handler_flushes_on_error(logger):
    buffer_handler = BufferingHandler(10)
    handler = LimitedMemoryHandler(max_len=10, target=buffer_handler)
    logger.addHandler(handler)

    logger.info("1")
    logger.info("2")
    logger.error("3")

    # empty memory buffer
    assert len(handler.buffer) == 0
    # flush to target
    assert len(buffer_handler.buffer) == 3
    assert buffer_handler.buffer[0].msg == "1"
    assert buffer_handler.buffer[1].msg == "2"
    assert buffer_handler.buffer[2].msg == "3"


def test_limited_memory_not_flushes_on_close(logger):
    buffer_handler = BufferingHandler(10)
    handler = LimitedMemoryHandler(max_len=10, target=buffer_handler)
    logger.addHandler(handler)

    logger.info("1")
    logger.info("2")
    logger.info("3")

    handler.close()

    # we don't flush to target
    assert len(buffer_handler.buffer) == 0
    # disconnect from target
    assert handler.target is None


def test_limited_memory_handler_flushes_on_close(logger):
    buffer_handler = BufferingHandler(10)
    handler = LimitedMemoryHandler(max_len=10, target=buffer_handler, flushOnClose=True)
    logger.addHandler(handler)

    logger.info("1")
    logger.info("2")
    logger.info("3")

    handler.close()

    # we flush to target
    assert len(buffer_handler.buffer) == 3
    assert buffer_handler.buffer[0].msg == "1"
    assert buffer_handler.buffer[1].msg == "2"
    assert buffer_handler.buffer[2].msg == "3"
    # disconnect from target
    assert handler.target is None
