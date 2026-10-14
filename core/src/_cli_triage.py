"""CLI handler: triage - modelo e esforco recomendados para a demanda (D-153)."""

from __future__ import annotations

import argparse
import json

from _constants import PROCESS_FILE
from _state import read_json
from _tasks import find_task_or_current, save_task
from _triage import describe, recommend


def cmd_triage(args: argparse.Namespace) -> int:
    """Com sinais, recalcula e grava; sem, mostra a triagem gravada."""
    task = find_task_or_current(args.task_id)
    signals = args.scope is not None or args.risk or args.uncertain or args.irreversible
    if signals:
        task["triage"] = recommend(task, read_json(PROCESS_FILE, {}), args.scope or 1, list(args.risk),
                                   bool(args.uncertain), bool(args.irreversible))
        save_task(task)
    triage = task.get("triage")
    if args.json:
        print(json.dumps({"task": task["id"], "triage": triage}, ensure_ascii=False, indent=2))
        return 0
    if not triage:
        print(f"{task['id']}: sem triagem. Informe os sinais: triage {task['id']} --scope N [--risk X] [--uncertain] [--irreversible]")
        return 0
    print(f"MODELO RECOMENDADO {task['id']}: {describe(triage)}")
    return 0


__all__ = ["cmd_triage"]
