"""O quadro do chat controlador (D-210, ADR-0025, estende a ADR-0023).

A D-199 escreveu quem e controlador e quem e executora; o controlador ainda
montava o estado de tudo juntando notas soltas de cada chat. Aqui o motor
monta o quadro a partir das demandas:

- as executoras de cada controlador, com etapa, PR e com quem esta a bola
  (dono, fila ou executora - tirado do mesmo `next_step` que conduz a demanda);
- as perguntas ao dono gravadas na demanda (`ask`), juntas, e a resposta citada
  que volta a executora (`answer`);
- as follow-ups propostas (Planejada/Backlog com o controlador herdado e sem
  sessao): so o controlador abre a sessao;
- as sessoes de demandas ja concluidas, para o controlador propor arquivar;
- as vagas: `controller.maxExecutors` executoras abertas ao mesmo tempo.

O motor nao fala com o app: lista, grava e diz a linha que o chat executa.
"""

from __future__ import annotations

from typing import Any

from _chat_sync import valid_session
from _clock import now_iso
from _conductor import STEP_STOP, next_step
from _constants import (
    STATUS_BACKLOG,
    STATUS_BLOCKED,
    STATUS_CANCELLED,
    STATUS_FINISHED,
    STATUS_INTEGRATED,
    STATUS_PLANNED,
    STATUS_VALIDATED,
)

MAX_EXECUTORS_DEFAULT = 4
# Concluida para a executora: o trabalho dela acabou (Integrada: o finish e do dono, D-204).
_DONE = (STATUS_INTEGRATED, STATUS_FINISHED, STATUS_VALIDATED, STATUS_CANCELLED)
_PROPOSED = (STATUS_PLANNED, STATUS_BACKLOG)
BALL_OWNER, BALL_QUEUE, BALL_EXECUTOR = "dono", "fila", "executora"
_QUEUE_OWNERS = ("fila", "gerente da fila")


def max_executors(config: dict[str, Any]) -> int:
    value = (config.get("controller") or {}).get("maxExecutors")
    return value if isinstance(value, int) and value > 0 else MAX_EXECUTORS_DEFAULT


def controller_of(task: dict[str, Any]) -> str | None:
    return (task.get("chat") or {}).get("controller")


def _session(task: dict[str, Any]) -> str | None:
    session = (task.get("chat") or {}).get("session")
    return session if valid_session(session) else None


def _archived(task: dict[str, Any]) -> bool:
    return bool((task.get("chat") or {}).get("archived"))


# ---- perguntas ao dono -------------------------------------------------------

def open_questions(task: dict[str, Any]) -> list[dict[str, Any]]:
    return [q for q in task.get("decisions") or [] if not q.get("answer")]


def ask(task: dict[str, Any], question: str, options: list[str], by: str | None) -> dict[str, Any]:
    """Grava a pergunta na demanda; o id (P1, P2...) e por demanda."""
    decisions = task.setdefault("decisions", [])
    entry = {
        "id": f"P{len(decisions) + 1}",
        "question": question.strip(),
        "options": [o.strip() for o in options if o.strip()],
        "askedBy": by or _session(task),
        "askedAt": now_iso(),
        "answer": None,
    }
    decisions.append(entry)
    return entry


def answer(task: dict[str, Any], question_id: str, quote: str, by: str | None) -> dict[str, Any]:
    """Grava a resposta do dono, com as palavras dele, na pergunta aberta."""
    wanted = question_id.strip().upper()
    for entry in task.get("decisions") or []:
        if entry.get("id") == wanted:
            if entry.get("answer"):
                raise SystemExit(f"{task['id']} {wanted} ja foi respondida: \"{entry['answer']['quote']}\".")
            entry["answer"] = {"quote": quote.strip(), "by": by, "at": now_iso()}
            return entry
    raise SystemExit(f"{task['id']} nao tem a pergunta {wanted} (veja `guia controle`).")


def deliver_line(task: dict[str, Any], entry: dict[str, Any]) -> str:
    """A linha que o controlador leva a executora: a resposta citada, nunca parafraseada."""
    to = entry.get("askedBy") or _session(task) or "<sessao da executora>"
    return f"LEVE A EXECUTORA: {to} <- {task['id']} {entry['id']}: o dono disse \"{entry['answer']['quote']}\""


# ---- o quadro ----------------------------------------------------------------

def ball(task: dict[str, Any], config: dict[str, Any]) -> tuple[str, str]:
    """(com quem esta a bola, por que) - pergunta aberta e do dono antes de tudo."""
    pending = open_questions(task)
    if pending:
        return BALL_OWNER, f"{len(pending)} pergunta(s) pendente(s)"
    if task.get("status") == STATUS_BLOCKED:
        return BALL_OWNER, "bloqueada"
    step = next_step(task, config)
    if step["step"] != STEP_STOP or step.get("owner") == "agente":
        return BALL_EXECUTOR, f"{step['step']}: {step['why']}"
    if step.get("owner") in _QUEUE_OWNERS:
        return BALL_QUEUE, step["why"]
    return BALL_OWNER, step["why"]


def _row(task: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    who, why = ball(task, config)
    return {
        "task": task["id"],
        "kind": task.get("kind"),
        "title": task.get("title"),
        "status": task.get("status"),
        "pr": (task.get("pr") or {}).get("number"),
        "session": _session(task),
        "ball": who,
        "why": why,
        "questions": open_questions(task),
    }


def board(tasks: list[dict[str, Any]], config: dict[str, Any], controller: str | None = None) -> list[dict[str, Any]]:
    """Um bloco por controlador (ou so o pedido): executoras, propostas, a arquivar, vagas."""
    controllers = [controller] if controller else sorted({c for t in tasks if (c := controller_of(t))})
    limit = max_executors(config)
    blocks = []
    for ctrl in controllers:
        mine = [t for t in tasks if controller_of(t) == ctrl]
        active = [t for t in mine if t.get("status") not in _DONE + _PROPOSED and not _archived(t)]
        blocks.append({
            "controller": ctrl,
            "limit": limit,
            "active": len(active),
            "free": max(limit - len(active), 0),
            "executors": [_row(t, config) for t in active],
            "proposed": [{"task": t["id"], "title": t.get("title"), "status": t.get("status"),
                          "from": t.get("proposedFrom")}
                         for t in mine if t.get("status") in _PROPOSED and not _session(t)],
            "archive": [{"task": t["id"], "status": t.get("status"), "session": _session(t)}
                        for t in mine if t.get("status") in _DONE and _session(t) and not _archived(t)],
        })
    return blocks


def inherit_controller(task: dict[str, Any], origin: dict[str, Any]) -> None:
    """D-210: a follow-up proposta herda o controlador da origem e espera a sessao dele."""
    task["proposedFrom"] = origin["id"]
    role = (origin.get("chat") or {}).get("role")
    ctrl = controller_of(origin) if role == "executor" else _session(origin) if role == "controller" else None
    if ctrl:
        task["chat"] = {"role": "executor", "controller": ctrl, "at": now_iso()}


__all__ = [
    "BALL_EXECUTOR",
    "BALL_OWNER",
    "BALL_QUEUE",
    "MAX_EXECUTORS_DEFAULT",
    "answer",
    "ask",
    "ball",
    "board",
    "controller_of",
    "deliver_line",
    "inherit_controller",
    "max_executors",
    "open_questions",
]
