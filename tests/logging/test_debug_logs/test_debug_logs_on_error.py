from __future__ import annotations

import os
import re

import pytest

from .package_file import do_smth

from cloudshell.logging.qs_logger import get_qs_logger
from cloudshell.logging.utils.venv import get_venv_name

venv_name = get_venv_name()


def test_no_debug_logs(tmp_path):
    rid = "reservation id"
    file_prefix = "resource_name"
    os.environ["LOG_PATH"] = str(tmp_path)

    _ = get_qs_logger(log_category="tests", log_file_prefix=file_prefix, log_group=rid)
    do_smth(rid, error=False)

    folder_path = tmp_path / rid / venv_name
    file_paths = list(folder_path.glob(f"{file_prefix}*.log"))
    assert len(file_paths) == 1
    log_records = file_paths[0].read_text()

    assert len(re.findall(r"do smth with", log_records)) == 1
    assert f"info do smth with {rid}" in log_records
    assert f"debug do smth with {rid}" not in log_records


def test_debug_logs_on_error(tmp_path):
    rid = "reservation id"
    file_prefix = "resource_name"
    os.environ["LOG_PATH"] = str(tmp_path)

    _ = get_qs_logger(log_category="tests", log_file_prefix=file_prefix, log_group=rid)
    with pytest.raises(ZeroDivisionError):
        do_smth(rid, error=True)

    folder_path = tmp_path / rid / venv_name
    file_paths = list(folder_path.glob(f"{file_prefix}*.log"))
    assert len(file_paths) == 2

    if "debug" in file_paths[0].name:
        debug_log_path, info_log_path = file_paths
    else:
        info_log_path, debug_log_path = file_paths

    info_log_records = info_log_path.read_text()
    assert len(re.findall(r"do smth with", info_log_records)) == 1
    assert f"info do smth with {rid}" in info_log_records
    assert f"debug do smth with {rid}" not in info_log_records

    debug_log_records = debug_log_path.read_text()
    assert len(re.findall(r"do smth with", debug_log_records)) == 2
    assert f"info do smth with {rid}" in debug_log_records
    assert f"debug do smth with {rid}" in debug_log_records
