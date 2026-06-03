"""CLI handlers: feature / issue / backlog / promote.

Handles task creation and backlog -> task promotion.

Fix vs the previous monolithic ai.py:
- cmd_promote (achado 2.2): build the task FIRST, only persist the
  backlog pop AFTER the task and worktree succeed. The old code
  popped+wrote the backlog before creating the task; a failure in
  create_promoted_task / attach_worktree would silently lose the item.
"""

from __future__ import annotations

import argparse
from typing import Any

from _clock import today
from _constants import KIND_FEATURE, MSG_BACKLOG_ITEM_NOT_FOUND, BACKLOG_FILE, TASKS_FILE
from _features_md import upsert_features_entry
from _state import read_json, write_json
from _tasks import (
    merge_list,
    new_task,
    next_backlog_id,
    next_task_id,
    pop_item,
    print_task_created,
    set_current_task,
)
from _worktree import attach_worktree


def cmd_create_task(args: argparse.Namespace, kind: str) -> int:
    data = read_json(TASKS_FILE, {"schemaVersion": 1, "tasks": []})
    task_id = next_task_id(kind, data.get("tasks", []))
    task = new_task(task_id, kind, args.title, args.context, args.origin)
    data.setdefault("tasks", []).insert(0, task)
    write_json(TASKS_FILE, data)
    set_current_task(task)
    upsert_features_entry(task)
    print_task_created(task)
    return 0


def cmd_backlog_add(args: argparse.Namespace) -> int:
    data = read_json(BACKLOG_FILE, {"schemaVersion": 1, "items": []})
    item_id = next_backlog_id(data.get("items", []))
    item = {
        "id": item_id,
        "title": args.title,
        "context": args.context,
        "status": "Backlog",
        "createdAt": today(),
        "updatedAt": today(),
    }
    data.setdefault("items", []).insert(0, item)
    write_json(BACKLOG_FILE, data)
    print(f"{item_id} added to backlog: {args.title}")
    return 0


def cmd_backlog_list(_args: argparse.Namespace) -> int:
    data = read_json(BACKLOG_FILE, {"schemaVersion": 1, "items": []})
    for item in data.get("items", []):
        print(f"{item['id']} [{item['status']}] {item['title']}")
    return 0


def _create_promoted_task(args: argparse.Namespace, item: dict[str, Any]) -> dict[str, Any]:
    data = read_json(TASKS_FILE, {"schemaVersion": 1, "tasks": []})
    task_id = next_task_id(args.kind, data.get("tasks", []))
    title = args.title or f"{item['id']}: {item['title']}"
    context = args.context or f"Backlog {item['id']}: {item.get('context') or item['title']}"
    task = new_task(task_id, args.kind, title, context, f"Backlog {item['id']} ({today()})")
    task["backlogId"] = item["id"]
    task["assessment"] = args.assessment
    task["executionPlan"] = args.plan
    task["summary"] = ["Backlog promovido via ai-process."]
    if args.assessment:
        merge_list(task, "summary", [f"Avaliacao IA: {args.assessment[0]}"])
    if args.plan:
        merge_list(task, "pending", ["Executar plano aprovado antes da implementacao."])
    return task


def cmd_promote(args: argparse.Namespace) -> int:
    backlog = read_json(BACKLOG_FILE, {"schemaVersion": 1, "items": []})
    items = backlog.get("items", [])
    item = next((it for it in items if it.get("id") == args.backlog_id), None)
    if item is None:
        raise SystemExit(MSG_BACKLOG_ITEM_NOT_FOUND.format(id=args.backlog_id))

    # Build everything BEFORE mutating disk. Only the worktree command
    # actually touches the filesystem early; if it fails, we abort here
    # without having popped the backlog item.
    task = _create_promoted_task(args, item)
    if args.worktree:
        attach_worktree(task, args, item)

    # Now persist: pop backlog, append task, set current, upsert MD.
    pop_item(items, args.backlog_id)
    write_json(BACKLOG_FILE, backlog)

    tasks_data = read_json(TASKS_FILE, {"schemaVersion": 1, "tasks": []})
    tasks_data.setdefault("tasks", []).insert(0, task)
    write_json(TASKS_FILE, tasks_data)

    set_current_task(task)
    upsert_features_entry(task)
    print_task_created(task)
    if task.get("worktree", {}).get("path"):
        print(f"WORKTREE_PATH={task['worktree']['path']}")
    return 0


__all__ = [
    "cmd_create_task",
    "cmd_backlog_add",
    "cmd_backlog_list",
    "cmd_promote",
]
