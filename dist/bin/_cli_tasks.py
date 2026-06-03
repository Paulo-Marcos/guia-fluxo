"""CLI handlers: tasks list / show / filter (F-017).

Navegacao read-only de `.ai/tasks.json`. Reaproveita _tasks.list_tasks
e _tasks.format_task_line; tudo suporta --json para consumo por agente.
"""

from __future__ import annotations

import argparse
import json

from _tasks import find_task, format_task_line, list_tasks


def _print_json(payload) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def cmd_tasks_list(args: argparse.Namespace) -> int:
    items = list_tasks(limit=args.limit)
    if args.json:
        _print_json({"count": len(items), "tasks": items})
        return 0
    if not items:
        print("Nenhuma task registrada.")
        return 0
    for task in items:
        print(format_task_line(task))
    return 0


def cmd_tasks_show(args: argparse.Namespace) -> int:
    task = find_task(args.task_id)
    if task is None:
        if args.json:
            _print_json({"found": False, "taskId": args.task_id})
        else:
            print(f"Task nao encontrada: {args.task_id}")
        return 1
    if args.json:
        _print_json(task)
    else:
        print(json.dumps(task, ensure_ascii=False, indent=2))
    return 0


def cmd_tasks_filter(args: argparse.Namespace) -> int:
    items = list_tasks(status=args.status, kind=args.kind, limit=args.limit)
    if args.json:
        _print_json(
            {
                "filters": {"status": args.status, "kind": args.kind, "limit": args.limit},
                "count": len(items),
                "tasks": items,
            }
        )
        return 0
    if not items:
        print("Nenhuma task bate com o filtro.")
        return 0
    for task in items:
        print(format_task_line(task))
    return 0


__all__ = ["cmd_tasks_list", "cmd_tasks_show", "cmd_tasks_filter"]
