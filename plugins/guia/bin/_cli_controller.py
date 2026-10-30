"""CLI handlers: controle, ask, answer - o controlador concentra as decisoes (D-210, ADR-0025)."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from typing import Any

from _chat_sync import MSG_BAD_SESSION, valid_session
from _clock import today
from _constants import PROCESS_FILE, TASKS_FILE
from _controller import answer, ask, board, deliver_line
from _state import file_lock, read_json, replace_json
from _tasks import TASKS_LOCK, find_task_or_current, kind_marker, list_tasks


def cmd_controle(args: argparse.Namespace) -> int:
    """O quadro do controlador: executoras, perguntas, propostas, a arquivar e vagas."""
    controller = (args.session or "").strip() or None
    if controller and not valid_session(controller):
        raise SystemExit(MSG_BAD_SESSION.format(session=controller))
    blocks = board(list_tasks(), read_json(PROCESS_FILE, {}), controller)
    if args.json:
        print(json.dumps(blocks, ensure_ascii=False, indent=2))
        return 0
    if not blocks:
        print("Nenhuma demanda com controlador gravado (chat D-NNN --controller <sessionId>).")
    for block in blocks:
        _print_block(block)
    return 0


def _print_block(block: dict[str, Any]) -> None:
    over = " - ACIMA DO LIMITE: nao abra sessao nova" if block["active"] > block["limit"] else ""
    print(f"CONTROLADOR {block['controller']} - executoras {block['active']} de {block['limit']} "
          f"({block['free']} vaga(s)){over}")
    for row in block["executors"]:
        pr = f" · PR #{row['pr']}" if row["pr"] else ""
        print(f"  {row['task']} {kind_marker(row['kind'] or '')} {row['status']}{pr} · bola: {row['ball']} "
              f"({row['why']}) · sessao {row['session'] or '-'}")
        for q in row["questions"]:
            options = f" [opcoes: {' | '.join(q['options'])}]" if q["options"] else ""
            print(f"    PERGUNTA {row['task']} {q['id']}: {q['question']}{options}")
    for item in block["proposed"]:
        origin = f" (proposta por {item['from']})" if item["from"] else ""
        vaga = "abra a sessao" if block["free"] else "SEM VAGA: espera"
        print(f"  PROPOSTA {item['task']} {item['status']}{origin}: {item['title']} - {vaga} (so o controlador abre)")
    for item in block["archive"]:
        print(f"  ARQUIVE COM OK DO DONO: {item['session']} ({item['task']} {item['status']}) - "
              f"depois: chat {item['task']} --archived")


def _locked_update(task_id: str, change: Callable[[dict[str, Any]], Any]) -> tuple[dict[str, Any], Any]:
    """Le-muda-grava a demanda sob a trava do tasks.json: um `ask` e um `answer`
    ao mesmo tempo nao apagam um ao outro, e o id P<n> nao se repete."""
    with file_lock(TASKS_LOCK):
        data = read_json(TASKS_FILE, {"schemaVersion": 1, "tasks": []})
        task = next(t for t in data.get("tasks", []) if t.get("id") == task_id)
        result = change(task)
        task["updatedAt"] = today()
        replace_json(TASKS_FILE, data)
    return task, result


def _session_arg(value: str | None) -> str | None:
    session = (value or "").strip() or None
    if session and not valid_session(session):
        raise SystemExit(MSG_BAD_SESSION.format(session=session))
    return session


def cmd_ask(args: argparse.Namespace) -> int:
    """A executora grava a pergunta ao dono na demanda, em vez de mandar uma mensagem por vez."""
    task_id = find_task_or_current(args.task_id)["id"]
    by = _session_arg(args.by)
    task, entry = _locked_update(task_id, lambda t: ask(t, args.question, args.option or [], by))
    controller = (task.get("chat") or {}).get("controller")
    where = f"o controlador ({controller})" if controller else "o dono"
    print(f"PERGUNTA {task['id']} {entry['id']} gravada; {where} a ve em `guia controle` e responde com "
          f"`guia answer {task['id']} {entry['id']} --quote \"<palavras do dono>\"`.")
    return 0


def cmd_answer(args: argparse.Namespace) -> int:
    """O controlador grava a resposta do dono, citada, e diz a quem leva-la."""
    task_id = find_task_or_current(args.task_id)["id"]
    by = _session_arg(args.by)
    task, entry = _locked_update(task_id, lambda t: answer(t, args.question_id, args.quote, by))
    print(deliver_line(task, entry))
    return 0


def add_controller_parsers(sub: Any) -> None:
    p_ctrl = sub.add_parser(
        "controle",
        help="D-210 (ADR-0025): o quadro do chat controlador - executoras com etapa, PR e bola (dono, fila, "
             "executora), perguntas pendentes, follow-ups propostas, sessoes a arquivar e vagas.",
    )
    p_ctrl.add_argument("--session", metavar="SESSION", help="So este controlador (sessionId); sem ele, todos.")
    p_ctrl.add_argument("--json", action="store_true", help="Saida em JSON.")
    p_ctrl.set_defaults(func=cmd_controle)

    p_ask = sub.add_parser("ask", help="D-210: a executora grava uma pergunta ao dono na demanda (fila de decisoes).")
    p_ask.add_argument("task_id", help="A demanda que pergunta (D-NNN).")
    p_ask.add_argument("question", help="A pergunta, curta.")
    p_ask.add_argument("--option", action="append", metavar="OPCAO", help="Uma opcao (repetivel).")
    p_ask.add_argument("--by", metavar="SESSION", help="sessionId de quem pergunta (default: a sessao da demanda).")
    p_ask.set_defaults(func=cmd_ask)

    p_answer = sub.add_parser("answer", help="D-210: o controlador grava a resposta do dono, citada, a uma pergunta.")
    p_answer.add_argument("task_id", help="A demanda (D-NNN).")
    p_answer.add_argument("question_id", help="A pergunta (P1, P2...).")
    p_answer.add_argument("--quote", required=True, help="As palavras do dono, sem parafrasear.")
    p_answer.add_argument("--by", metavar="SESSION", help="sessionId do controlador que repassa.")
    p_answer.set_defaults(func=cmd_answer)


__all__ = ["add_controller_parsers", "cmd_answer", "cmd_ask", "cmd_controle"]
