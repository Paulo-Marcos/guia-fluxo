"""CLI handler: next - o proximo passo da demanda, decidido pelo motor (D-152)."""

from __future__ import annotations

import argparse
import json

from _conductor import next_step
from _constants import PROCESS_FILE
from _state import read_json
from _tasks import find_task_or_current


def cmd_next(args: argparse.Namespace) -> int:
    task = find_task_or_current(args.task_id)
    step = next_step(task, read_json(PROCESS_FILE, {}))
    if args.json:
        print(json.dumps({"task": task["id"], **step}, ensure_ascii=False, indent=2))
        return 0
    owner = f" (destrava: {step['owner']})" if step["owner"] else ""
    print(f"{task['id']} [nivel {step['level']}]: {step['step']} - {step['why']}{owner}")
    return 0


__all__ = ["cmd_next"]
