"""Task domain: shape, identity, persistence.

Public surface:
    new_task(...)               build a fresh task dict
    next_task_id(kind, tasks)   compute next F-NNN/I-NNN id
    next_backlog_id(items)      compute next B-NNN id
    find_task(id)               lookup in tasks.json
    find_task_or_current(id)    resolve from current-task.json if id missing
    save_task(task)             upsert in tasks.json
    merge_list(task, key, vals) idempotent list append
    pop_item(items, id)         find+remove from backlog list
    set_current_task(task)      write current-task.json + chat-title

No I/O outside the .ai/ files defined in _constants.
"""

from __future__ import annotations

import re
import sys
from typing import Any

from _clock import today
from _constants import (
    BACKLOG_FILE,
    CHAT_TITLE_FILE,
    CHAT_TITLE_FORMAT_DEFAULT,
    CURRENT_FILE,
    FEATURES_FILE,
    KIND_FEATURE,
    KIND_MARKER_FALLBACK,
    KIND_MARKERS,
    MSG_DEFAULT_TASK_CREATED,
    MSG_DEFAULT_TASK_PENDING,
    MSG_NO_CURRENT_TASK,
    MSG_TASK_NOT_FOUND,
    PREFIX_DEMANDA,
    PREFIX_FEATURE,
    PREFIX_ISSUE,
    PROCESS_FILE,
    STATUS_BACKLOG,
    STATUS_IN_DEVELOPMENT,
    STATUS_TAGS,
    TASK_HEADING_RE,
    TASK_PREFIXES_FOR_NUMBERING,
    TASKS_FILE,
)
from _state import read_json, read_text, write_json


def new_task(
    task_id: str,
    kind: str,
    title: str,
    context: str,
    origin: str,
    status: str = STATUS_IN_DEVELOPMENT,
) -> dict[str, Any]:
    """Build a fresh task dict.

    `status` defaults to `STATUS_IN_DEVELOPMENT` (preserva comportamento de
    feature/issue/promote). Backlog (ADR-0011 Fase 2) cria a task ja com
    `status=STATUS_BACKLOG` - nao houve implementacao ainda, entao tambem
    nao listamos `modifiedFiles` nem semeamos `summary`/`pending` com
    defaults de implementacao.
    """
    is_backlog = status == STATUS_BACKLOG
    task: dict[str, Any] = {
        "id": task_id,
        "kind": kind,
        "title": title,
        "status": status,
        "origin": origin,
        "context": context or title,
        "createdAt": today(),
        "updatedAt": today(),
        "modifiedFiles": [] if is_backlog else [FEATURES_FILE.name],
        "summary": [] if is_backlog else [MSG_DEFAULT_TASK_CREATED],
        "validations": [],
        "pending": [] if is_backlog else [MSG_DEFAULT_TASK_PENDING],
    }
    return task


def _number_from_id(value: str, prefix: str) -> int | None:
    match = re.fullmatch(rf"{prefix}-(\d+)", value or "")
    return int(match.group(1)) if match else None


def _numbers_from_features(prefix: str) -> list[int]:
    if not FEATURES_FILE.exists():
        return []
    return [
        int(match.group(2))
        for match in TASK_HEADING_RE.finditer(read_text(FEATURES_FILE))
        if match.group(1) == prefix
    ]


def next_task_id(_kind: str, tasks: list[dict[str, Any]]) -> str:
    """Gera o proximo ID neutro `D-NNN` (ADR-0011 Fase 1).

    O parametro `kind` e ignorado: ID e independente do tipo da demanda.
    Numeracao e monotonica considerando todos os prefixos vivos
    (D, F, I) em `tasks.json` e em `FEATURES.md`, de modo que `D-030`
    nunca colida visualmente com `F-029` ja existente. `B-NNN` fica de
    fora desta contagem ate a Fase 2 (backlog absorvido).
    """
    numbers: list[int] = []
    for prefix in TASK_PREFIXES_FOR_NUMBERING:
        numbers.extend(
            value
            for value in (_number_from_id(task.get("id", ""), prefix) for task in tasks)
            if value is not None
        )
        numbers.extend(_numbers_from_features(prefix))
    next_number = max(numbers, default=0) + 1
    return f"{PREFIX_DEMANDA}-{next_number:03d}"


def find_task(task_id: str) -> dict[str, Any] | None:
    data = read_json(TASKS_FILE, {"tasks": []})
    return next((task for task in data.get("tasks", []) if task.get("id") == task_id), None)


def recent_task_ids(limit: int = 5) -> list[str]:
    data = read_json(TASKS_FILE, {"tasks": []})
    return [task.get("id", "") for task in data.get("tasks", [])[:limit] if task.get("id")]


def list_tasks(
    status: str | None = None,
    kind: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Return tasks matching the optional filters.

    Filters are exact-match against task['status'] and task['kind'].
    The list comes ordered as stored in tasks.json (newest first by
    convention - cmd_create_task inserts at index 0).
    """
    data = read_json(TASKS_FILE, {"tasks": []})
    items = list(data.get("tasks", []))
    if status:
        items = [t for t in items if t.get("status") == status]
    if kind:
        items = [t for t in items if t.get("kind") == kind]
    if limit is not None:
        items = items[:limit]
    return items


def format_task_line(task: dict[str, Any]) -> str:
    """Compact one-line representation for `tasks list` output.

    Inclui o marcador visual do kind (emoji) entre o ID e o status,
    permitindo distinguir feature/bug/chore a olho no listing.
    """
    marker = kind_marker(task.get("kind", ""))
    return (
        f"{task.get('id', '?')} {marker} "
        f"[{task.get('status', '?')}] {task.get('title', '')}"
    )


def find_task_or_current(task_id: str | None) -> dict[str, Any]:
    current = read_json(CURRENT_FILE, {})
    chosen_id = task_id or current.get("taskId")
    if not chosen_id:
        raise SystemExit(MSG_NO_CURRENT_TASK)
    task = find_task(chosen_id)
    if task is None:
        suggestions = recent_task_ids()
        hint = f" Recent: {', '.join(suggestions)}" if suggestions else ""
        raise SystemExit(MSG_TASK_NOT_FOUND.format(id=chosen_id) + hint)
    return task


def save_task(updated: dict[str, Any]) -> None:
    data = read_json(TASKS_FILE, {"schemaVersion": 1, "tasks": []})
    for index, task in enumerate(data.get("tasks", [])):
        if task.get("id") == updated.get("id"):
            updated["updatedAt"] = today()
            data["tasks"][index] = updated
            write_json(TASKS_FILE, data)
            return
    raise SystemExit(MSG_TASK_NOT_FOUND.format(id=updated.get("id")))


def pop_item(items: list[dict[str, Any]], item_id: str) -> dict[str, Any] | None:
    for index, item in enumerate(items):
        if item.get("id") == item_id:
            return items.pop(index)
    return None


def merge_list(task: dict[str, Any], key: str, values: list[str]) -> None:
    current = list(task.get(key, []))
    for value in values:
        if value and value not in current:
            current.append(value)
    task[key] = current


def status_tag(status: str) -> str:
    return STATUS_TAGS.get(status, status.upper().replace(" ", "_"))


def kind_marker(kind: str) -> str:
    """Emoji que representa o `kind` da demanda em superficies de display.

    Fallback `•` quando `kind` esta vazio ou e desconhecido (defesa
    em profundidade: tasks novas sempre tem kind setado por
    cmd_create_task / cmd_backlog_add / cmd_promote).
    """
    return KIND_MARKERS.get(kind or "", KIND_MARKER_FALLBACK)


def chat_title(task: dict[str, Any]) -> str:
    template = read_json(PROCESS_FILE, {}).get(
        "chatTitleFormat",
        CHAT_TITLE_FORMAT_DEFAULT,
    )
    return template.format(
        id=task["id"],
        kindMarker=kind_marker(task.get("kind", "")),
        statusTag=status_tag(task["status"]),
        title=task["title"],
    )


def current_task_payload(task: dict[str, Any]) -> dict[str, str]:
    return {
        "taskId": task["id"],
        "status": task["status"],
        "title": task["title"],
        "chatTitle": chat_title(task),
    }


def set_current_task(task: dict[str, Any]) -> None:
    write_json(CURRENT_FILE, current_task_payload(task))
    CHAT_TITLE_FILE.write_text(chat_title(task) + "\n", encoding="utf-8")


def print_chat_title(task: dict[str, Any]) -> None:
    print(f"\nNOME DO CHAT: {chat_title(task)}")
    print(f"CHAT_TITLE={chat_title(task)}")


def print_task_created(task: dict[str, Any]) -> None:
    print(f"{task['id']} created: {task['title']}")
    print_chat_title(task)


__all__ = [
    "new_task",
    "next_task_id",
    "find_task",
    "find_task_or_current",
    "save_task",
    "pop_item",
    "merge_list",
    "status_tag",
    "kind_marker",
    "chat_title",
    "current_task_payload",
    "set_current_task",
    "print_chat_title",
    "print_task_created",
    "recent_task_ids",
    "list_tasks",
    "format_task_line",
]
