"""A fila de integracao (D-126, R5): estado atomico, ordem e espera.

`.guia/queue.json` e local (mora na arvore principal, fora do git) e e
escrito por varios chats ao mesmo tempo. Toda escrita passa por `mutate`:
trava de arquivo criada com `O_EXCL` (so um processo consegue), leitura,
mudanca, gravacao num temporario e `os.replace` (troca atomica). Trava de um
processo morto expira, para nao travar a fila para sempre.
"""

from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from typing import Any, Callable, Iterator

from _constants import GUIA_DIR

QUEUE_FILE = GUIA_DIR / "queue.json"
LOCK_FILE = GUIA_DIR / "queue.lock"
LOCK_TIMEOUT_SECONDS = 30.0
LOCK_STALE_SECONDS = 120.0
PRIORITY_HOTFIX = "hotfix"
PRIORITY_NORMAL = "normal"
STATE_WAITING = "waiting"
OPEN_STATES = frozenset({STATE_WAITING, "integrating"})
_TERMINAL = frozenset({"Validada", "Finalizada", "Resolvida", "Cancelada", "Integrada"})


def _empty() -> dict[str, Any]:
    return {"schemaVersion": 1, "paused": False, "pausedReason": None, "frozenReason": None, "items": []}


@contextmanager
def _locked() -> Iterator[None]:
    deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            try:
                if time.time() - LOCK_FILE.stat().st_mtime > LOCK_STALE_SECONDS:
                    LOCK_FILE.unlink(missing_ok=True)
                    continue
            except FileNotFoundError:
                continue
            if time.monotonic() > deadline:
                raise SystemExit(f"Fila ocupada: {LOCK_FILE} ha mais de {LOCK_TIMEOUT_SECONDS:.0f}s.")
            time.sleep(0.02)
    try:
        os.write(fd, str(os.getpid()).encode("ascii"))
        os.close(fd)
        yield
    finally:
        LOCK_FILE.unlink(missing_ok=True)


def load() -> dict[str, Any]:
    if not QUEUE_FILE.exists():
        return _empty()
    return {**_empty(), **json.loads(QUEUE_FILE.read_text(encoding="utf-8"))}


def _save(data: dict[str, Any]) -> None:
    temporary = QUEUE_FILE.with_name(f"{QUEUE_FILE.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, QUEUE_FILE)


def mutate(change: Callable[[dict[str, Any]], Any]) -> Any:
    """Le, muda e grava a fila sob a trava; devolve o retorno de `change`."""
    with _locked():
        data = load()
        result = change(data)
        _save(data)
        return result


def waiting_reason(item: dict[str, Any], status_of: Callable[[str], str | None]) -> str | None:
    """Por que o item ainda nao integra (None = elegivel)."""
    if item.get("state") != STATE_WAITING:
        return f"estado {item.get('state')}"
    open_deps = [dep for dep in item.get("dependsOn") or [] if status_of(dep) not in _TERMINAL]
    if open_deps:
        return f"depende de {', '.join(open_deps)} (aberta)"
    if not item.get("approval"):
        return "sem aprovacao de merge (guia approve)"
    return None


def ordered(items: list[dict[str, Any]], status_of: Callable[[str], str | None]) -> list[tuple[dict[str, Any], str | None]]:
    """Itens na ordem de integracao (hotfix a frente, depois FIFO), com o motivo de espera."""
    ranked = sorted(items, key=lambda i: (i.get("priority") != PRIORITY_HOTFIX, i.get("enqueuedAt") or ""))
    return [(item, waiting_reason(item, status_of)) for item in ranked]


def find(data: dict[str, Any], task_id: str) -> dict[str, Any] | None:
    return next((item for item in data["items"] if item["id"] == task_id), None)


__all__ = [
    "LOCK_FILE",
    "OPEN_STATES",
    "PRIORITY_HOTFIX",
    "PRIORITY_NORMAL",
    "QUEUE_FILE",
    "STATE_WAITING",
    "find",
    "load",
    "mutate",
    "ordered",
    "waiting_reason",
]
