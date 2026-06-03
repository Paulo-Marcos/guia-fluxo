"""Path helpers used across modules.

Separated from _constants because these are functions, not literals.
"""

from __future__ import annotations

import re
from pathlib import Path

from _constants import ROOT


def relative(path: Path) -> str:
    """Return path as POSIX-style relative to ROOT.

    Falls back to the absolute POSIX form if the path is outside the
    repository (used in error messages where exactness matters more than
    pretty output).
    """
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def normalize_path(value: str) -> str:
    """Normalize a filesystem path string for comparison.

    Backslashes become slashes (Windows fix), leading `./` is stripped,
    and surrounding whitespace is trimmed. Used everywhere paths are
    compared by value (lock matching, staged-vs-declared check).
    """
    return value.replace("\\", "/").lstrip("./").strip()


def slugify(value: str, max_length: int = 80) -> str:
    """Lowercase ASCII slug with safe length bound."""
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return cleaned[:max_length] or "task"


__all__ = ["relative", "normalize_path", "slugify"]
