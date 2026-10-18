"""CLI handler: chat - em que chat a demanda e feita, para voltar a ele (D-157)."""

from __future__ import annotations

import argparse
import json

from _clock import now_iso
from _tasks import chat_name, find_task_or_current, save_task


def cmd_chat(args: argparse.Namespace) -> int:
    """Sem `--title`/`--session`, mostra o nome sugerido e o gravado; com eles, grava.

    D-188: `--session` guarda o id da sessao do app junto do nome, para a fila
    pedir ao chat gerente que renomeie esse chat quando a demanda integrar.
    """
    task = find_task_or_current(args.task_id)
    session = (args.session or "").strip()
    if args.title or session:
        chat = dict(task.get("chat") or {})
        if args.title:
            chat["title"] = args.title.strip()
        if session:
            chat["session"] = session
        chat["at"] = now_iso()
        task["chat"] = chat
        save_task(task)
    recorded = (task.get("chat") or {}).get("title")
    recorded_session = (task.get("chat") or {}).get("session")
    if args.json:
        print(json.dumps({"task": task["id"], "suggested": chat_name(task), "chat": recorded,
                          "session": recorded_session}, ensure_ascii=False, indent=2))
        return 0
    print(f"NOME DO CHAT: {recorded or chat_name(task)}")
    if not recorded:
        print(f"(sugerido; grave com: chat {task['id']} --title \"<nome do chat>\")")
    if recorded_session:
        print(f"SESSAO DO CHAT: {recorded_session}")
    return 0


__all__ = ["cmd_chat"]
