"""CLI handler: model - o modelo usado na demanda, ao lado do recomendado (D-154)."""

from __future__ import annotations

import argparse
import json

from _models_used import record, summary
from _tasks import find_task_or_current, list_tasks, save_task


def _print_entries(task: dict) -> None:
    entries = task.get("modelsUsed") or []
    if not entries:
        print(f"{task['id']}: nenhum modelo registrado.")
    for entry in entries:
        print(f"  {task['id']} {entry['who']}: {entry['model']} ({entry['purpose']}) - "
              f"recomendado {entry['recommended'] or '?'}: {entry['vs']}")


def cmd_model(args: argparse.Namespace) -> int:
    """Grava um uso (--who/--model/--purpose), mostra os da demanda, ou --summary de todas."""
    if args.summary:
        result = summary(list_tasks())
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        counts = result["counts"]
        print("Modelo usado x recomendado: " + ", ".join(f"{k}: {v}" for k, v in counts.items()))
        for item in result["above"]:
            print(f"  acima: {item['task']} {item['who']} {item['model']} (recomendado {item['recommended']}) - {item['purpose']}")
        return 0
    task = find_task_or_current(args.task_id)
    if args.model:
        entry = record(task, args.who, args.model, args.purpose or "trabalho na demanda", args.effort)
        save_task(task)
        if args.json:
            print(json.dumps(entry, ensure_ascii=False, indent=2))
            return 0
        print(f"MODELO USADO {task['id']}: {entry['who']} {entry['model']} ({entry['purpose']}) - "
              f"recomendado {entry['recommended'] or '?'}: {entry['vs']}")
        return 0
    if args.json:
        print(json.dumps({"task": task["id"], "modelsUsed": task.get("modelsUsed") or []}, ensure_ascii=False, indent=2))
        return 0
    _print_entries(task)
    return 0


__all__ = ["cmd_model"]
