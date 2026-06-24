"""CLI handlers: tasks list / show / filter (F-017).

Navegacao read-only de `.guia/tasks.json`. Reaproveita _tasks.list_tasks
e _tasks.format_task_line; tudo suporta --json para consumo por agente.
"""

from __future__ import annotations

import argparse
import json

from _stats import compute_stats, format_duration
from _tasks import find_task, find_task_or_current, format_task_line, list_tasks


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


def cmd_stats(args: argparse.Namespace) -> int:
    """D-052: timing/throughput de uma task (elapsed total, tempo ativo,
    bloqueios, ciclos de ready). Aceita id explicito ou cai no current-task.
    `--json` para consumo por agente."""
    task = find_task_or_current(args.task_id)
    stats = compute_stats(task)
    if args.json:
        _print_json({"taskId": task["id"], "stats": stats})
        return 0
    print(f"{task['id']} {task.get('title', '')}")
    print(f"  startedAt : {stats['startedAt'] or '-'}")
    print(f"  readyAt   : {stats['readyAt'] or '-'}")
    print(f"  finishedAt: {stats['finishedAt'] or '-'}")
    print(f"  elapsed total : {format_duration(stats['elapsedTotalSeconds'])}")
    print(f"  blocked total : {format_duration(stats['elapsedBlockedSeconds'])}")
    print(f"  active time   : {format_duration(stats['activeTimeSeconds'])}")
    print(f"  blocks/unblocks: {stats['blockCount']}/{stats['unblockCount']}")
    print(f"  ready cycles   : {stats['readyCount']}")
    return 0


__all__ = ["cmd_tasks_list", "cmd_tasks_show", "cmd_tasks_filter", "cmd_stats"]
