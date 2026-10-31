"""CLI handler: next - o proximo passo da demanda, decidido pelo motor (D-152)."""

from __future__ import annotations

import argparse
import json

from _artifacts import artifacts_dir
from _chat_sync import pending_renames, rename_line
from _conductor import next_step
from _constants import PROCESS_FILE, STATUS_IN_QUEUE
from _executor_spawn import ensure_executor
from _state import read_json
from _tasks import find_task_or_current


def cmd_next(args: argparse.Namespace) -> int:
    task = find_task_or_current(args.task_id)
    config = read_json(PROCESS_FILE, {})
    started = None
    if task.get("status") == STATUS_IN_QUEUE:
        # D-204: o chat que acompanha a demanda na fila religa o executor que saiu
        # (item esperando CI, ou o primeiro ainda subindo); idempotente pelo lease.
        started = ensure_executor(task, config)
    step = next_step(task, config)
    if args.json:
        # D-194: qualquer chat que pergunta o proximo passo ve os nomes atrasados.
        # D-202: o lugar dos artefatos (auditoria, logs) vem junto, para nao
        # cairem na pasta pai.
        payload = {"task": task["id"], **step, "executor": started, "chatRenames": pending_renames(),
                   "artifactsDir": str(artifacts_dir(task["id"]))}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if started:
        print(started)
    owner = f" (destrava: {step['owner']})" if step["owner"] else ""
    chat = f" [chat: {step['chat']}]" if step.get("chat") else ""
    print(f"{task['id']} [nivel {step['level']}]: {step['step']} - {step['why']}{owner}{chat}")
    for pending in pending_renames():
        print(rename_line(pending))
    if step.get("chatWarning"):
        print(step["chatWarning"])
    return 0


__all__ = ["cmd_next"]
