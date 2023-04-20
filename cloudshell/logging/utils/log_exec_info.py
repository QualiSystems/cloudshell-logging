from __future__ import annotations

import logging
from collections.abc import Collection


def log_execution_info(
    logger: logging.Logger,
    exec_info: dict[str, dict[str, str] | dict[str, Collection[str]]],
) -> None:
    """Log provided execution information into provided logger.

    :param logger: logger to log execution info into
    :param exec_info: execution info to log
       {LOG_LEVEL: {KEY: VALUE}}
       VALUE can be a list of strings
    """
    log_fn_map = {
        "DEBUG": logger.debug,
        "INFO": logger.info,
        "WARNING": logger.warning,
        "ERROR": logger.error,
    }

    logger.info("--------------- Execution Info: ---------------------------")
    for log_level, info in exec_info.items():
        log_fn = log_fn_map[log_level.upper()]
        for k, v in info.items():
            if isinstance(v, list):
                v = "\n\t".join(v)
                v = f"\n\t{v}"
            log_fn(f"{k.ljust(20)}: {v}")
    logger.info("-----------------------------------------------------------\n")
