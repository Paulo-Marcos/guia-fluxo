"""Bridge to the standalone lock_api module.

In the plugins/guia/ layout (consumer), `guia.py` and `lock_api.py` sit
side by side under `plugins/guia/bin/`, so `import lock_api` just works.
In the repo-mae, `lock_api.py` lives in `core/lock/`, so we add that
directory to `sys.path` before importing.

This module wraps the import + offers the small adapter ai.py needs:
`lock_task_files`, which now goes through the shared API instead of
hand-rolling YAML strings (achado 2.Q3 / 5.Q1).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from _clock import today
from _constants import (
    FEATURES_FILE,
    FEATURES_REL,
    MSG_LOCK_ALREADY_EXISTS,
    MSG_LOCK_ID_REQUIRED,
    MSG_NO_FILES_TO_LOCK,
    MSG_NONE_PLACEHOLDER,
    REGISTRY_FILE,
)


def _ensure_lock_api_importable() -> None:
    here = Path(__file__).resolve().parent
    sibling = here.parent / "lock"  # repo-mae layout
    candidates = [here, sibling]
    for candidate in candidates:
        path_str = str(candidate)
        if candidate.exists() and path_str not in sys.path:
            sys.path.insert(0, path_str)


_ensure_lock_api_importable()

import lock_api  # noqa: E402  (path setup above)


def lock_task_files(
    task: dict[str, Any],
    lock_id: str | None,
    description: str | None,
) -> None:
    """Register a lock for files touched by `task`.

    Files excluded from the registry block:
      - .guia/DEMANDAS.md (auto-managed)
      - .guia/locks/registry.yaml (the registry itself)
      - the "Nenhuma." placeholder
    """
    excluded = {FEATURES_REL, ".guia/locks/registry.yaml", MSG_NONE_PLACEHOLDER}
    files = [value for value in task.get("modifiedFiles", []) if value not in excluded]
    if not lock_id:
        raise SystemExit(MSG_LOCK_ID_REQUIRED)
    if not files:
        raise SystemExit(MSG_NO_FILES_TO_LOCK)
    try:
        lock_api.append_lock_block(
            lock_id=lock_id,
            files=files,
            description=description or task["title"],
            locked_at=today(),
        )
    except lock_api.LockExists:
        raise SystemExit(MSG_LOCK_ALREADY_EXISTS.format(id=lock_id))
    except lock_api.LockIgnoredPath as exc:
        raise SystemExit(
            f"Lock recusado: {exc.args[0]} esta em .guia/locks/lock-ignore.txt"
        )
    except lock_api.LockOutsideRepo as exc:
        raise SystemExit(f"Lock recusado: path traversal ({exc.args[0]})")


__all__ = ["lock_api", "lock_task_files"]
