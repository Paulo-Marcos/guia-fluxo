"""Low-level state I/O: JSON read/write, write-if-missing.

Kept tiny and dependency-free so domain modules can import freely. No
business logic; just persistence primitives.
"""

from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

LOCK_TIMEOUT_SECONDS = 30.0
LOCK_STALE_SECONDS = 120.0
_RETRY_SECONDS = 0.02
# No Windows, arquivo em exclusao pendente ou aberto por outro processo devolve
# PermissionError, nao FileExistsError: contencao passageira (D-132).
_BUSY = (FileExistsError, PermissionError)


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any, readable: bool = False) -> None:
    """Grava o JSON. `readable` (D-159) e para arquivo versionado que o dono le
    (o process.json): acento e emoji como texto e quebra de linha LF - sem ele,
    o emoji vira escape \\uXXXX e o Windows grava CRLF, diff a toa no git."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=not readable, indent=2) + "\n",
        encoding="utf-8",
        newline="\n" if readable else None,
    )


@contextmanager
def file_lock(lock: Path) -> Iterator[None]:
    """Trava entre processos por `O_EXCL` (D-204), o mesmo desenho da fila (D-126)."""
    deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
    lock.parent.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except _BUSY:
            try:
                if time.time() - lock.stat().st_mtime > LOCK_STALE_SECONDS:
                    lock.unlink(missing_ok=True)
                    continue
            except (FileNotFoundError, PermissionError):
                pass
            if time.monotonic() > deadline:
                raise SystemExit(f"{lock} ocupado ha mais de {LOCK_TIMEOUT_SECONDS:.0f}s.")
            time.sleep(_RETRY_SECONDS)
    try:
        os.write(fd, str(os.getpid()).encode("ascii"))
        os.close(fd)
        yield
    finally:
        _retry(lambda: lock.unlink(missing_ok=True), lock)


def _retry(action: Any, path: Path) -> None:
    deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
    while True:
        try:
            action()
            return
        except PermissionError:
            if time.monotonic() > deadline:
                raise SystemExit(f"{path} bloqueado por outro processo ha mais de {LOCK_TIMEOUT_SECONDS:.0f}s.")
            time.sleep(_RETRY_SECONDS)


def replace_json(path: Path, payload: Any) -> None:
    """Grava por arquivo temporario + troca: quem le no meio nunca ve JSON pela metade."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    _retry(lambda: os.replace(temporary, path), path)


def write_if_missing(path: Path, payload: Any, force: bool = False) -> None:
    if path.exists() and not force:
        return
    write_json(path, payload)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def copy_if_missing(src: Path, dst: Path, force: bool = False) -> bool:
    """Copy `src` -> `dst` byte-for-byte unless `dst` already exists.

    Returns True when it wrote, False when it preserved an existing file.
    Creates parent dirs. Byte copy (not text) keeps the exact bytes and
    newlines - it matters for the POSIX commit-msg hook, which must stay
    LF to run under sh on Linux/Mac. Used by `init` to deploy per-project
    templates without ever clobbering existing state (D-076).
    """
    if dst.exists() and not force:
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())
    return True


__all__ = ["read_json", "write_json", "write_if_missing", "read_text", "copy_if_missing"]
