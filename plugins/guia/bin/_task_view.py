"""Leitura humana de uma demanda (D-192): o que ela vai fazer e onde esta.

Uma visao so, usada em dois lugares: o `status D-NNN` no terminal (texto) e
o detalhe do cartao no painel (dict). Funcoes puras sobre o dict da task -
nada aqui le o `ROOT` global, porque o painel olha varios projetos.
"""

from __future__ import annotations

from typing import Any

# Etapas em que a falta de plano importa: a demanda ja foi triada e vai ser
# (ou esta sendo) feita. Backlog ainda e ideia; o resto ja passou da hora.
PLAN_EXPECTED_STATUSES = frozenset({"Planejada", "Em desenvolvimento"})
# D-199 (ADR-0023): o papel do chat que faz a demanda.
ROLES = {"controller": "controlador", "executor": "executora"}


def role_line(chat: dict[str, Any] | None) -> str | None:
    """`executora (controlador local_...)`, `controlador`, ou None sem papel."""
    role = ROLES.get((chat or {}).get("role") or "")
    if not role:
        return None
    controller = (chat or {}).get("controller")
    return f"{role} (controlador {controller})" if controller else role


MISSING_PLAN = "Sem plano registrado: grave os passos com `plan D-NNN --step \"...\"` (ou `start --step`)."


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [v for v in value or [] if isinstance(v, str) and v.strip()]


def _chat(chat: dict[str, Any]) -> dict[str, Any]:
    """Nome e sessao; papel e controlador (D-199) so quando gravados."""
    out = {"title": chat.get("title"), "session": chat.get("session")}
    out.update({k: chat[k] for k in ("role", "controller") if chat.get(k)})
    return out


def plan_steps(task: dict[str, Any]) -> list[str]:
    return _strings(task.get("executionPlan"))


def missing_plan(task: dict[str, Any]) -> bool:
    status = task.get("status")
    return status in PLAN_EXPECTED_STATUSES and task.get("kind") != "epic" and not plan_steps(task)


def timeline(task: dict[str, Any]) -> list[dict[str, str]]:
    """Etapas pelas quais a demanda passou, pelos carimbos que o motor grava.
    A task nao guarda um historico de transicoes; isto reconstroi o que da."""
    pr = task.get("pr") or {}
    audit = task.get("audit") or {}
    events: list[tuple[str, str]] = [
        ("Criada", task.get("createdAt")),
        ("Em desenvolvimento", task.get("startedAt")),
        ("Aguardando validacao", task.get("readyAt")),
        (f"PR #{pr.get('number')}" if pr.get("number") else "PR", pr.get("shippedAt")),
        (f"Auditoria: {audit.get('result')}" if audit.get("result") else "Auditoria", audit.get("at")),
        ("Fechada", task.get("finishedAt") or task.get("resolvedAt")),
    ]
    for block in task.get("blocks") or []:
        if isinstance(block, dict):
            events.append((f"Bloqueada: {block.get('reason', '')}".rstrip(": "), block.get("at")))
            events.append(("Desbloqueada", block.get("unblockedAt")))
    for cancel in task.get("cancellations") or []:
        if isinstance(cancel, dict):
            events.append((f"Cancelada: {cancel.get('reason', '')}".rstrip(": "), cancel.get("at")))
    steps = [{"step": label, "at": str(at)} for label, at in events if at]
    steps.sort(key=lambda s: s["at"][:10])  # estavel: no mesmo dia, mantem a ordem do fluxo
    return steps


def detail(task: dict[str, Any]) -> dict[str, Any]:
    """O que o dono precisa para entender a demanda, sem o JSON inteiro."""
    chat = task.get("chat") or {}
    triage = task.get("triage") or {}
    worktree = task.get("worktree") or {}
    return {
        "context": task.get("context") or "",
        "origin": task.get("origin") or "",
        "assessment": _strings(task.get("assessment")),
        "plan": plan_steps(task),
        "missingPlan": missing_plan(task),
        "files": _strings(task.get("modifiedFiles")),
        "summary": _strings(task.get("summary")),
        "validations": _strings(task.get("validations")),
        "pending": _strings(task.get("pending")),
        "requests": [
            {"request": r.get("request", ""), "test": r.get("test", "")}
            for r in task.get("requestToTest") or [] if isinstance(r, dict)
        ],
        "chat": _chat(chat) if chat.get("title") else None,
        "triage": {"model": triage.get("model"), "effort": triage.get("effort"), "tier": triage.get("tier")} if triage else None,
        "branch": worktree.get("branch"),
        "dependsOn": _strings(task.get("dependsOn")),
        "steps": timeline(task),
    }


def _section(lines: list[str], title: str, items: list[str], numbered: bool = False) -> None:
    if not items:
        return
    lines.append("")
    lines.append(f"{title}:")
    for index, item in enumerate(items, start=1):
        lines.append(f"  {index}. {item}" if numbered else f"  - {item}")


def format_text(task: dict[str, Any], marker: str = "") -> str:
    """O `status D-NNN` legivel: cabecalho, contexto e as listas que importam."""
    info = detail(task)
    lines = [f"{task.get('id')} {marker} {task.get('title', '')}".replace("  ", " ").strip()]
    meta = [f"Etapa: {task.get('status', '?')}", f"tipo {task.get('kind', '?')}"]
    if info["triage"] and info["triage"].get("model"):
        meta.append(f"modelo {info['triage']['model']}/{info['triage'].get('effort') or '?'}")
    if info["branch"]:
        meta.append(f"branch {info['branch']}")
    pr = task.get("pr") or {}
    if pr.get("number"):
        meta.append(f"PR #{pr['number']}")
    lines.append("  " + " · ".join(meta))
    if info["chat"]:
        role = role_line(info["chat"])
        lines.append(f"  Chat: {info['chat']['title']}" + (f" · {role}" if role else ""))
    if info["context"]:
        lines.append("")
        lines.append("Contexto:")
        lines.append(f"  {info['context']}")
    if info["missingPlan"]:
        lines.append("")
        lines.append(f"! {MISSING_PLAN.replace('D-NNN', str(task.get('id')))}")
    _section(lines, "Plano", info["plan"], numbered=True)
    _section(lines, "Arquivos", info["files"])
    _section(lines, "Resumo", info["summary"])
    _section(lines, "Validacoes", info["validations"])
    _section(lines, "Pendencias", info["pending"])
    _section(lines, "Pedido -> Teste", [f"{r['request']} -> {r['test']}" for r in info["requests"]])
    _section(lines, "Etapas", [f"{s['at'][:16].replace('T', ' ')}  {s['step']}" for s in info["steps"]])
    lines.append("")
    lines.append(f"(JSON completo: status {task.get('id')} --json)")
    return "\n".join(lines)


__all__ = ["MISSING_PLAN", "ROLES", "detail", "format_text", "missing_plan", "plan_steps", "role_line", "timeline"]
