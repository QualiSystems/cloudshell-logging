from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def do_smth(name: str) -> None:
    logger.info(f"do smth with {name}")
