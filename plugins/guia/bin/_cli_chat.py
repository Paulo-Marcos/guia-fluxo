"""CLI handler: chat - em que chat a demanda e feita, para voltar a ele (D-157)."""

from __future__ import annotations

import argparse
import json
from typing import Any

from _chat_sync import (
    MSG_BAD_SESSION,
    mark_applied,
    mark_refused,
    missing_line,
    missing_sessions,
    pending_renames,
    rename_line,
    valid_session,
)
from _clock import now_iso
from _controller import DONE_STATUSES
from _task_view import role_line
from _tasks import chat_name, find_task_or_current, save_task


def cmd_chat(args: argparse.Namespace) -> int:
    """Sem `--title`/`--session`, mostra o nome sugerido e o gravado; com eles, grava.

    D-188: `--session` guarda o id da sessao do app junto do nome, para a fila
    pedir ao chat gerente que renomeie esse chat quando a demanda integrar.
    D-194: `--pending` lista as sessoes com nome atrasado; `--applied` e
    `--refused` registram o que o chat fez com cada uma.
    D-199 (ADR-0023): `--role` e `--controller` dizem se quem faz a demanda e
    uma executora e qual chat controlador a abriu.
    D-210 (ADR-0025): `--archived`/`--unarchived` registram a sessao arquivada.
    """
    if args.pending:
        return _print_pending(args.json)
    task = find_task_or_current(args.task_id)
    if args.applied or args.refused:
        return _confirm(task, args)
    if args.archived or args.unarchived:
        return _archive(task, args.archived)
    session = (args.session or "").strip()
    if session and not valid_session(session):
        raise SystemExit(MSG_BAD_SESSION.format(session=session))
    controller = (args.controller or "").strip()
    if controller and not valid_session(controller):
        raise SystemExit(MSG_BAD_SESSION.format(session=controller))
    role = args.role or ("executor" if controller else None)
    if role == "controller" and controller:
        raise SystemExit("--controller vale para a executora; o controlador nao tem controlador.")
    if args.title or session or role:
        chat = dict(task.get("chat") or {})
        if args.title:
            chat["title"] = args.title.strip()
        if session and session != chat.get("session"):
            # Sessao nova: o nome aplicado/recusado era da anterior.
            chat.pop("applied", None)
            chat.pop("refused", None)
            chat["session"] = session
        if role:
            chat["role"] = role
            if controller:
                chat["controller"] = controller
            elif role == "controller":
                chat.pop("controller", None)
        chat["at"] = now_iso()
        task["chat"] = chat
        save_task(task)
    recorded = (task.get("chat") or {}).get("title")
    recorded_session = (task.get("chat") or {}).get("session")
    chat = task.get("chat") or {}
    if args.json:
        print(json.dumps({"task": task["id"], "suggested": chat_name(task), "chat": recorded,
                          "session": recorded_session, "role": chat.get("role"),
                          "controller": chat.get("controller")}, ensure_ascii=False, indent=2))
        return 0
    print(f"NOME DO CHAT: {recorded or chat_name(task)}")
    if not recorded:
        print(f"(sugerido; grave com: chat {task['id']} --title \"<nome do chat>\")")
    if recorded_session:
        print(f"SESSAO DO CHAT: {recorded_session}")
    if role_line(chat):
        print(f"PAPEL DO CHAT: {role_line(chat)}")
    return 0


def _print_pending(as_json: bool) -> int:
    pending = pending_renames()
    missing = missing_sessions()
    if as_json:
        print(json.dumps({"pending": pending, "missing": missing}, ensure_ascii=False, indent=2))
        return 0
    for item in pending:
        print(rename_line(item))
    if not pending:
        print("Nenhum chat com nome atrasado.")
    for item in missing:
        print(missing_line(item))
    return 0


def _archive(task: dict[str, Any], archived: bool) -> int:
    """D-210: a sessao concluida arquivada (com ok do dono) sai do quadro do `controle`."""
    chat = task.setdefault("chat", {})
    if archived and task.get("status") not in DONE_STATUSES:
        raise SystemExit(f"Recusado: {task['id']} esta {task.get('status')} - so se arquiva a sessao de demanda "
                         f"concluida ({', '.join(DONE_STATUSES)}).")
    if archived:
        chat["archived"] = now_iso()
        print(f"SESSAO ARQUIVADA: {task['id']} ({chat.get('session') or 'sem sessao'}) - desfaz com --unarchived.")
    else:
        chat.pop("archived", None)
        print(f"SESSAO REABERTA: {task['id']} ({chat.get('session') or 'sem sessao'}).")
    save_task(task)
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
