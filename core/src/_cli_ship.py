"""CLI handler: ship (D-122)."""

from __future__ import annotations

import argparse

from _constants import PROCESS_FILE
from _features_md import upsert_features_entry
from _ship import ship
from _state import read_json
from _tasks import find_task_or_current, print_demand_title, save_task, set_current_task


def cmd_ship(args: argparse.Namespace) -> int:
    """Leva a demanda do worktree ao PR; sem id, vale a branch (D-110)."""
    task = find_task_or_current(args.task_id)
    pr = ship(task, read_json(PROCESS_FILE, {}), args)
    save_task(task)
    set_current_task(task)
    upsert_features_entry(task)
    print(f"{task['id']} em PR: #{pr['number']} {pr['url']}")
    print_demand_title(task)
    return 0


__all__ = ["cmd_ship"]
