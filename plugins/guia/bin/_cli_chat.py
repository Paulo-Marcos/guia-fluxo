"""CLI handler: chat - em que chat a demanda e feita, para voltar a ele (D-157)."""

from __future__ import annotations

import argparse
import json

from _clock import now_iso
from _tasks import chat_name, find_task_or_current, save_task


def cmd_chat(args: argparse.Namespace) -> int:
    """Sem `--title`, mostra o nome sugerido e o gravado; com `--title`, grava."""
    task = find_task_or_current(args.task_id)
    if args.title:
        task["chat"] = {"title": args.title.strip(), "at": now_iso()}
        save_task(task)
    recorded = (task.get("chat") or {}).get("title")
    if args.json:
        print(json.dumps({"task": task["id"], "suggested": chat_name(task), "chat": recorded}, ensure_ascii=False, indent=2))
        return 0
    print(f"NOME DO CHAT: {recorded or chat_name(task)}")
    if not recorded:
        print(f"(sugerido; grave com: chat {task['id']} --title \"<nome do chat>\")")
    return 0


__all__ = ["cmd_chat"]
