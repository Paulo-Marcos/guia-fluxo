"""Shared helper to import the core modules in tests.

`core/src` is not on sys.path by default, and ai.py adds itself to
sys.path only when invoked as `__main__`. Tests need explicit setup.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CORE_SRC = REPO_ROOT / "core" / "src"
CORE_LOCK = REPO_ROOT / "core" / "lock"


def ensure_core_importable() -> None:
    for candidate in (CORE_SRC, CORE_LOCK):
        path_str = str(candidate)
        if candidate.exists() and path_str not in sys.path:
            sys.path.insert(0, path_str)


__all__ = ["REPO_ROOT", "CORE_SRC", "CORE_LOCK", "ensure_core_importable"]
