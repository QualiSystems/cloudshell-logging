import logging

from cloudshell.logging.utils.error_handling_context_manager import (
    ErrorHandlingContextManager,
)

logger = logging.getLogger(__name__)


def do_smth(name: str, error: bool) -> None:
    with ErrorHandlingContextManager(logger):
        logger.debug(f"debug do smth with {name}")
        logger.info(f"info do smth with {name}")
        if error:
            1 / 0
