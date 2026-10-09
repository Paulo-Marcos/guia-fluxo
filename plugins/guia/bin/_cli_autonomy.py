"""CLI handler: autonomy (D-133)."""

from __future__ import annotations

import argparse
import json

from _autonomy import LEVELS, effective_level, set_level, settings
from _constants import PROCESS_FILE
from _state import read_json
from _tasks import find_task_or_current, print_demand_title, save_task, set_current_task


def cmd_autonomy(args: argparse.Namespace) -> int:
    """`autonomy [nivel] [D-NNN]`: sem nivel, mostra; com nivel, grava na demanda."""
    level = next((token for token in args.tokens if token in LEVELS), None)
    others = [token for token in args.tokens if token not in LEVELS]
    if len(others) > 1 or (others and not others[0].upper().startswith(("D-", "E-"))):
        raise SystemExit(f"Nivel invalido em {others}: use {', '.join(LEVELS)} e, opcional, o id da demanda.")
    task = find_task_or_current(others[0] if others else None)
    config = read_json(PROCESS_FILE, {})
    if level:
        set_level(task, level, args.by, config)
        save_task(task)
        set_current_task(task)
    conf = settings(config)
    shown = {
        "id": task["id"],
        "level": (task.get("autonomy") or {}).get("level"),
        "effective": effective_level(task, config),
        "default": conf["default"],
        "ceiling": conf["ceiling"],
        "setBy": (task.get("autonomy") or {}).get("setBy"),
    }
    if args.json:
        print(json.dumps(shown, ensure_ascii=False, indent=2))
        return 0
    print(f"{task['id']}: autonomia {shown['effective']} (padrao {conf['default']}, teto {conf['ceiling']})")
    print_demand_title(task)
    return 0


__all__ = ["cmd_autonomy"]
