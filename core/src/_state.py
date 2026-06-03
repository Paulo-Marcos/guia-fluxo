"""Low-level state I/O: JSON read/write, write-if-missing.

Kept tiny and dependency-free so domain modules can import freely. No
business logic; just persistence primitives.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def write_if_missing(path: Path, payload: Any, force: bool = False) -> None:
    if path.exists() and not force:
        return
    write_json(path, payload)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


__all__ = ["read_json", "write_json", "write_if_missing", "read_text"]
