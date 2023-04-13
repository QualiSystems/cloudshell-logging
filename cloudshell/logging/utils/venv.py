from __future__ import annotations

import sys
from pathlib import Path


def get_venv_name() -> str:
    """Returns the name of the current venv or Python name."""
    return Path(sys.prefix).name
