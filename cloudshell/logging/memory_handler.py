from __future__ import annotations

import logging
from collections import deque


class LimitedMemoryHandler(logging.Handler):
    def __init__(
        self,
        max_len: int,
        target: logging.Handler,
        flushLevel: int = logging.ERROR,
        flushOnClose: bool = False,
        level: int = logging.NOTSET,
    ):
        super().__init__(level=level)
        self.max_len = max_len
        self.flushLevel = flushLevel
        self.target = target
        self.flushOnClose = flushOnClose
        self.buffer = deque(maxlen=max_len)

    def change_max_len(self, max_len: int) -> None:
        self.acquire()
        try:
            if self.max_len != max_len:
                self.max_len = max_len
                self.buffer = deque(self.buffer, maxlen=max_len)
        finally:
            self.release()

    def emit(self, record: logging.LogRecord) -> None:
        self.buffer.append(record)
        if self.shouldFlush(record):
            self.flush()

    def shouldFlush(self, record: logging.LogRecord) -> bool:
        return record.levelno >= self.flushLevel

    def flush(self) -> None:
        self.acquire()
        try:
            if self.target:
                for record in self.buffer:
                    self.target.handle(record)
                self.buffer.clear()
        finally:
            self.release()

    def close(self) -> None:
        try:
            if self.flushOnClose:
                self.flush()
        finally:
            self.acquire()
            try:
                self.target = None
                super().close()
            finally:
                self.release()
