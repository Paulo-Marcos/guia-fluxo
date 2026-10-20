"""CLI handler: next - o proximo passo da demanda, decidido pelo motor (D-152)."""

from __future__ import annotations

import argparse
import json

from _chat_sync import pending_renames, rename_line
from _conductor import next_step
from _constants import PROCESS_FILE
from _state import read_json
from _tasks import find_task_or_current


def cmd_next(args: argparse.Namespace) -> int:
    task = find_task_or_current(args.task_id)
    step = next_step(task, read_json(PROCESS_FILE, {}))
    if args.json:
        # D-194: qualquer chat que pergunta o proximo passo ve os nomes atrasados.
        print(json.dumps({"task": task["id"], **step, "chatRenames": pending_renames()}, ensure_ascii=False, indent=2))
        return 0
    owner = f" (destrava: {step['owner']})" if step["owner"] else ""
    chat = f" [chat: {step['chat']}]" if step.get("chat") else ""
    print(f"{task['id']} [nivel {step['level']}]: {step['step']} - {step['why']}{owner}{chat}")
    for pending in pending_renames():
        print(rename_line(pending))
    return 0


__all__ = ["cmd_next"]
