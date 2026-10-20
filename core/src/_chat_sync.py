"""Reconciliar o nome dos chats com a etapa da demanda (D-194).

A D-188 deixava o rename final para o chat gerente da fila ler a linha do
`queue run`; com o executor num terminal ninguem a lia e o chat ficava com o
nome velho. Agora a demanda guarda o ultimo nome aplicado a sua sessao
(`chat.applied`) e qualquer chat do Guia que rode `chat --pending`, `next` ou
`status` ve as sessoes cujo nome divergiu do `NOME DA DEMANDA`, aplica e
confirma com `chat --applied`. Recusa (`chat --refused`) e lembrada com o
titulo recusado: vira aviso uma vez e so volta quando a etapa mudar.

O motor nao fala com o app; so compara, lista e grava.
"""

from __future__ import annotations

from typing import Any

from _tasks import demand_title, list_tasks

CHAT_RENAME_PREFIX = "RENOMEIE O CHAT: "

# O agente passa "self" para as tools do app; gravado, o literal nao aponta
# para sessao nenhuma (a D-191 gravou assim).
_PLACEHOLDERS = {"self", "<sessionid>", "sessionid"}

MSG_BAD_SESSION = (
    "Sessao invalida: '{session}'. Grave o id real da sessao - "
    "mcp__ccd_session_mgmt__get_session com session_id \"self\" devolve o sessionId "
    "(ex.: local_...); o literal \"self\" so vale dentro das tools do app."
)


def valid_session(session: str | None) -> bool:
    value = (session or "").strip()
    return bool(value) and value.lower() not in _PLACEHOLDERS and not any(c.isspace() for c in value)


def pending_rename(task: dict[str, Any]) -> dict[str, str] | None:
    """A renomeacao que falta nesta demanda, ou None (sem sessao valida, ja
    aplicada, ou recusada para este mesmo nome)."""
    chat = task.get("chat") or {}
    session = chat.get("session")
    if not valid_session(session):
        return None
    title = demand_title(task)
    if title in (chat.get("applied"), (chat.get("refused") or {}).get("title")):
        return None
    return {"task": task["id"], "session": session, "title": title}


def pending_renames() -> list[dict[str, str]]:
    return [p for p in (pending_rename(t) for t in list_tasks()) if p]


def rename_line(pending: dict[str, str]) -> str:
    return f"{CHAT_RENAME_PREFIX}{pending['session']} -> {pending['title']}"


def print_pending_renames() -> None:
    for pending in pending_renames():
        print(rename_line(pending))


def mark_applied(task: dict[str, Any], title: str) -> None:
    chat = task.setdefault("chat", {})
    chat["applied"] = title.strip()
    chat.pop("refused", None)


def mark_refused(task: dict[str, Any], title: str, reason: str | None) -> str:
    chat = task.setdefault("chat", {})
    chat["refused"] = {"title": title.strip(), "reason": (reason or "").strip() or None}
    why = f" ({reason.strip()})" if reason and reason.strip() else ""
    return (f"aviso: a sessao {chat.get('session')} recusou o nome '{title.strip()}'{why}; "
            f"nao sera pedido de novo ate a etapa de {task['id']} mudar - renomeie a mao se quiser.")


__all__ = [
    "CHAT_RENAME_PREFIX",
    "MSG_BAD_SESSION",
    "mark_applied",
    "mark_refused",
    "pending_rename",
    "pending_renames",
    "print_pending_renames",
    "rename_line",
    "valid_session",
]
