"""CLI handler: chat - em que chat a demanda e feita, para voltar a ele (D-157)."""

from __future__ import annotations

import argparse
import json
from typing import Any

from _chat_sync import MSG_BAD_SESSION, mark_applied, mark_refused, pending_renames, rename_line, valid_session
from _clock import now_iso
from _tasks import chat_name, find_task_or_current, save_task


def cmd_chat(args: argparse.Namespace) -> int:
    """Sem `--title`/`--session`, mostra o nome sugerido e o gravado; com eles, grava.

    D-188: `--session` guarda o id da sessao do app junto do nome, para a fila
    pedir ao chat gerente que renomeie esse chat quando a demanda integrar.
    D-194: `--pending` lista as sessoes com nome atrasado; `--applied` e
    `--refused` registram o que o chat fez com cada uma.
    """
    if args.pending:
        return _print_pending(args.json)
    task = find_task_or_current(args.task_id)
    if args.applied or args.refused:
        return _confirm(task, args)
    session = (args.session or "").strip()
    if session and not valid_session(session):
        raise SystemExit(MSG_BAD_SESSION.format(session=session))
    if args.title or session:
        chat = dict(task.get("chat") or {})
        if args.title:
            chat["title"] = args.title.strip()
        if session and session != chat.get("session"):
            # Sessao nova: o nome aplicado/recusado era da anterior.
            chat.pop("applied", None)
            chat.pop("refused", None)
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


def _print_pending(as_json: bool) -> int:
    pending = pending_renames()
    if as_json:
        print(json.dumps({"pending": pending}, ensure_ascii=False, indent=2))
        return 0
    for item in pending:
        print(rename_line(item))
    if not pending:
        print("Nenhum chat com nome atrasado.")
    return 0


def _confirm(task: dict[str, Any], args: argparse.Namespace) -> int:
    if args.applied:
        mark_applied(task, args.applied)
        save_task(task)
        print(f"NOME APLICADO: {task['id']} -> {args.applied.strip()}")
        return 0
    print(mark_refused(task, args.refused, args.reason))
    save_task(task)
    return 0


__all__ = ["cmd_chat"]
