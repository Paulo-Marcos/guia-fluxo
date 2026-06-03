"""Importable lock domain.

Single source of truth for lock matching, registry I/O and unlock parsing.
Consumed by:
    core/lock/check-lock.py    (thin CLI wrapper)
    core/src/ai.py             (lock_task_files in finish --lock)

DESIGN
------
- Pure data in/out where possible. Filesystem only inside _load_data,
  _save_locks, _load_lock_ignore (cached via functools.lru_cache for hot
  paths like the commit-msg hook walking 50 staged files).
- All path comparisons normalized via _norm to handle Windows
  backslashes (achado 2.4 / 5.19).
- Lock-ignore always wins, including when the lock pattern is `*` — the
  wildcard is treated like any other pattern so adding `.gitignore` to
  lock-ignore actually protects it (achado 5.Q4 / Q1 from etapa 5).
- Path traversal blocked: lock targets must resolve inside REPO_ROOT
  (achado 5.19).
- Unlock parsing requires `motivo:` somewhere after the marker in the
  same commit message (achado 5.14).

Operations vocabulary: add | modify | delete | rename.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Sequence

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - import-time guard
    raise SystemExit(
        "Erro: PyYAML nao instalado. Rode: pip install pyyaml"
    ) from exc


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY = REPO_ROOT / "features" / "registry.yaml"
LOCK_IGNORE = REPO_ROOT / "features" / "lock-ignore.txt"
ALL_OPERATIONS: tuple[str, ...] = ("add", "modify", "delete", "rename")
OPERATION_ADD, OPERATION_MODIFY, OPERATION_DELETE, OPERATION_RENAME = ALL_OPERATIONS

UNLOCK_RE = re.compile(r"\[unlock:([a-z0-9_\-]+)\]", re.IGNORECASE)
MOTIVO_RE = re.compile(r"motivo\s*:", re.IGNORECASE)

REGISTRY_HEADER = (
    "# Veja features/README.md para o protocolo e formato.\n"
    "# Edicao via CLI (recomendado): python core/lock/check-lock.py lock|unlock\n"
    "# Ou edite manualmente preservando o schema abaixo.\n"
    "\n"
)


# --- Domain types ----------------------------------------------------------


@dataclass(frozen=True)
class LockMatch:
    """A blocked (path, operation) pair tied to the lock that owns it."""

    path: str
    operation: str
    lock: dict


@dataclass(frozen=True)
class FileEvent:
    """A (path, operation) pair as inferred from git --name-status or args."""

    path: str
    operation: str


@dataclass
class LockSpec:
    """Spec to create a new lock via the API."""

    id: str
    description: str = ""
    operations: Sequence[str] = field(default_factory=lambda: ALL_OPERATIONS)
    files: Sequence[str] = ()


# --- Pure helpers ----------------------------------------------------------


def norm_path(value: str) -> str:
    """Normalize a path for comparison.

    Replaces backslashes with slashes, strips leading `./`, trims whitespace.
    """
    return value.replace("\\", "/").lstrip("./").strip()


def matches_pattern(pattern: str, path: str) -> bool:
    n_pattern = norm_path(pattern)
    n_path = norm_path(path)
    return n_pattern == n_path or fnmatchcase(n_path, n_pattern)


def infer_operation(path: str) -> str:
    """Infer add vs modify by whether the path currently exists on disk."""
    return OPERATION_MODIFY if (REPO_ROOT / path).exists() else OPERATION_ADD


# --- I/O (cached) ----------------------------------------------------------


@lru_cache(maxsize=1)
def _load_lock_ignore_cached() -> tuple[str, ...]:
    if not LOCK_IGNORE.exists():
        return ()
    lines: list[str] = []
    for line in LOCK_IGNORE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            lines.append(stripped)
    return tuple(lines)


def load_lock_ignore() -> list[str]:
    return list(_load_lock_ignore_cached())


def invalidate_caches() -> None:
    """Tests and long-running processes call this when files change."""
    _load_lock_ignore_cached.cache_clear()


def is_ignored_path(path: str) -> bool:
    return any(matches_pattern(pattern, path) for pattern in _load_lock_ignore_cached())


def _load_data() -> dict:
    if not REGISTRY.exists():
        return {"version": 1, "locks": []}
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return {"version": 1, "locks": []}
    data.setdefault("version", 1)
    if not data.get("locks"):
        data["locks"] = []
    return data


def load_locks() -> list[dict]:
    return _load_data().get("locks", []) or []


def save_locks(locks: list[dict]) -> None:
    data = {"version": 1, "locks": locks}
    body = yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )
    # Concurrency note: this rewrites the whole registry. Two parallel
    # writers would last-write-win. Acceptable for human-paced CLI use;
    # if scripted, gate via an external lock.
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(REGISTRY_HEADER + body, encoding="utf-8")


# --- Matching --------------------------------------------------------------


def lock_operations(lock: dict) -> set[str]:
    operations = lock.get("operations")
    if not operations:
        return set(ALL_OPERATIONS)
    return {norm_path(str(op)).lower() for op in operations}


def lock_matches(lock: dict, path: str, operation: str) -> bool:
    # Lock-ignore wins ALWAYS, including over the `*` wildcard. This makes
    # adding `.gitignore` to lock-ignore actually protect it from the
    # default "adicoes-exigem-autorizacao" blanket lock.
    if is_ignored_path(path):
        return False
    if operation not in lock_operations(lock):
        return False
    return any(matches_pattern(pattern, path) for pattern in lock.get("files", []) or [])


def find_blocked(events: Iterable[FileEvent]) -> list[LockMatch]:
    locks = load_locks()
    out: list[LockMatch] = []
    for event in events:
        for lock in locks:
            if lock_matches(lock, event.path, event.operation):
                out.append(LockMatch(event.path, event.operation, lock))
    return out


def unlocked_ids(message: str) -> set[str]:
    """Return lock ids unlocked by a commit message.

    A lock is "unlocked" iff:
      * the message contains `[unlock:<id>]` (case-insensitive)
      * AND the message contains `motivo:` somewhere after (any position
        in the message; achado 5.14 wants the rationale in the same
        commit message, not necessarily in the same line, since wrapping
        is normal).
    """
    if not message:
        return set()
    found = {match.group(1).lower() for match in UNLOCK_RE.finditer(message)}
    if not found:
        return set()
    if not MOTIVO_RE.search(message):
        return set()
    return found


def filter_unlocked(blocked: list[LockMatch], message: str) -> list[LockMatch]:
    unlocked = unlocked_ids(message)
    return [m for m in blocked if m.lock["id"].lower() not in unlocked]


# --- Event parsers ---------------------------------------------------------


def events_from_paths(paths: Iterable[str], operation: str | None = None) -> list[FileEvent]:
    return [FileEvent(p, operation or infer_operation(p)) for p in paths]


def events_from_name_status(lines: Iterable[str]) -> list[FileEvent]:
    events: list[FileEvent] = []
    for line in lines:
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        code = status[0]
        if code == "A" and len(parts) >= 2:
            events.append(FileEvent(parts[1], OPERATION_ADD))
        elif code == "M" and len(parts) >= 2:
            events.append(FileEvent(parts[1], OPERATION_MODIFY))
        elif code == "D" and len(parts) >= 2:
            events.append(FileEvent(parts[1], OPERATION_DELETE))
        elif code == "R" and len(parts) >= 3:
            old_path, new_path = parts[1], parts[2]
            events.extend(
                [
                    FileEvent(old_path, OPERATION_RENAME),
                    FileEvent(old_path, OPERATION_DELETE),
                    FileEvent(new_path, OPERATION_RENAME),
                    FileEvent(new_path, OPERATION_ADD),
                ]
            )
        elif code == "C" and len(parts) >= 3:
            events.append(FileEvent(parts[2], OPERATION_ADD))
        elif len(parts) == 1:
            events.extend(events_from_paths([parts[0]]))
    return events


# --- CRUD ------------------------------------------------------------------


class LockExists(Exception):
    pass


class LockNotFound(Exception):
    pass


class LockIgnoredPath(Exception):
    pass


class LockOutsideRepo(Exception):
    pass


def _path_inside_repo(path: str) -> bool:
    try:
        absolute = (REPO_ROOT / path).resolve()
        return absolute.is_relative_to(REPO_ROOT.resolve())
    except (OSError, ValueError):
        return False


def add_lock(
    spec: LockSpec,
    locked_at: str,
    allow_missing: bool = False,
) -> dict:
    locks = load_locks()
    if any(lock.get("id") == spec.id for lock in locks):
        raise LockExists(spec.id)

    norm_files: list[str] = []
    missing: list[str] = []
    for raw in spec.files:
        if raw != "*" and is_ignored_path(raw):
            raise LockIgnoredPath(raw)
        if raw != "*" and not _path_inside_repo(raw):
            raise LockOutsideRepo(raw)
        if raw != "*" and not (REPO_ROOT / raw).exists():
            missing.append(raw)
        norm_files.append(norm_path(raw))
    if missing and not allow_missing:
        raise FileNotFoundError(
            "Arquivos nao encontrados no repo: "
            + ", ".join(missing)
            + ". Use --allow-missing para travar futuro."
        )

    new_lock: dict = {
        "id": spec.id,
        "description": spec.description or "",
        "locked_at": locked_at,
        "operations": list(spec.operations),
        "files": norm_files,
    }
    locks.append(new_lock)
    save_locks(locks)
    invalidate_caches()
    return new_lock


def remove_lock(lock_id: str) -> None:
    locks = load_locks()
    remaining = [lock for lock in locks if lock.get("id") != lock_id]
    if len(remaining) == len(locks):
        raise LockNotFound(lock_id)
    save_locks(remaining)
    invalidate_caches()


def append_lock_block(
    lock_id: str,
    files: Sequence[str],
    description: str,
    locked_at: str,
) -> None:
    """Used by core/src/ai.py:lock_task_files to grow the registry.

    Goes through the API so behavior is consistent with the standalone
    CLI: lock-ignore is respected, paths are normalized, ignored paths
    cause an explicit error instead of silent override.
    """
    spec = LockSpec(
        id=lock_id,
        description=description,
        operations=ALL_OPERATIONS,
        files=files,
    )
    add_lock(spec, locked_at=locked_at, allow_missing=True)


__all__ = [
    "ALL_OPERATIONS",
    "OPERATION_ADD",
    "OPERATION_MODIFY",
    "OPERATION_DELETE",
    "OPERATION_RENAME",
    "REPO_ROOT",
    "REGISTRY",
    "LOCK_IGNORE",
    "UNLOCK_RE",
    "MOTIVO_RE",
    "REGISTRY_HEADER",
    "LockMatch",
    "FileEvent",
    "LockSpec",
    "LockExists",
    "LockNotFound",
    "LockIgnoredPath",
    "LockOutsideRepo",
    "norm_path",
    "matches_pattern",
    "infer_operation",
    "load_lock_ignore",
    "invalidate_caches",
    "is_ignored_path",
    "load_locks",
    "save_locks",
    "lock_operations",
    "lock_matches",
    "find_blocked",
    "unlocked_ids",
    "filter_unlocked",
    "events_from_paths",
    "events_from_name_status",
    "add_lock",
    "remove_lock",
    "append_lock_block",
]
