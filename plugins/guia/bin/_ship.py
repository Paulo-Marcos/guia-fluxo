"""`guia ship`: do worktree da demanda ao PR (D-122, R3/R4).

Todas as conferencias vem antes de qualquer efeito: se uma recusa, nada foi
empurrado, nenhum PR foi aberto e o estado nao mudou. Depois: push, PR
aberto ou atualizado (titulo = assunto do commit, corpo montado da demanda),
mensagem de squash gravada em `.guia/queue/<ID>.msg` e status `Em PR`.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from _changelog import changelog_settings, work_root
from _clock import now_iso
from _commit import compose_commit_message
from _constants import (
    DELIVERY_BASE_BRANCH_DEFAULT,
    DELIVERY_MODE,
    DELIVERY_MODE_PR,
    GUIA_DIR,
    STATUS_AWAITING_VALIDATION,
    STATUS_AWAITING_VALIDATION_ACCENTED,
    STATUS_IN_DEVELOPMENT,
    STATUS_IN_PR,
)
from _git_ops import current_branch, git_output
from _github import gh_pr_upsert

QUEUE_DIR = GUIA_DIR / "queue"
SHIPPABLE_STATUSES = frozenset({
    STATUS_IN_DEVELOPMENT,
    STATUS_AWAITING_VALIDATION,
    STATUS_AWAITING_VALIDATION_ACCENTED,
    STATUS_IN_PR,
})
REQUEST_TEST_SEPARATOR = "::"


def parse_request_test(raw: str) -> dict[str, str]:
    """`"pedido :: teste"` -> {request, test}; sem teste, fica "faltando"."""
    request, _sep, test = raw.partition(REQUEST_TEST_SEPARATOR)
    return {"request": request.strip(), "test": test.strip() or "faltando"}


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def build_pr_body(task: dict[str, Any], why: str | None, no_changelog: str | None, footer: str | None) -> str:
    parts = ["## O que muda e por quê", "", (why or "").strip() or f"{task['title']}.", ""]
    parts += ["## Pedido → Teste", "", "| Pedido | Teste |", "|---|---|"]
    parts += [f"| {_cell(item['request'])} | {_cell(item['test'])} |" for item in task.get("requestToTest", [])]
    parts.append("")
    if no_changelog:
        parts += [f"Sem fragmento de CHANGELOG: {no_changelog}", ""]
    parts.append(f"Demanda: {task['id']}")
    if footer:
        parts += ["", footer]
    return "\n".join(parts) + "\n"


def _refuse(message: str) -> None:
    raise SystemExit(f"ship recusado: {message}")


def _check_gate(root: Path, commands: list[str]) -> None:
    if not commands:
        print("Guia Fluxo: sem delivery.gate.full - portao NAO conferido pelo ship.", file=sys.stderr)
    for command in commands:
        try:
            result = subprocess.run(
                shlex.split(command, posix=os.name != "nt"),
                cwd=root, text=True, encoding="utf-8", errors="replace", capture_output=True,
            )
        except FileNotFoundError:
            _refuse(f"portao: comando nao encontrado: {command}")
        if result.returncode != 0:
            tail = "\n".join((result.stdout + result.stderr).strip().splitlines()[-15:])
            _refuse(f"portao falhou em `{command}` (exit {result.returncode}):\n{tail}")


def preflight(task: dict[str, Any], config: dict[str, Any], args: Any, cwd: Path) -> dict[str, Any]:
    """Todas as conferencias; devolve o contexto do envio. Nao muda nada."""
    if DELIVERY_MODE != DELIVERY_MODE_PR:
        _refuse("ship e do modo pr (delivery.mode = \"pr\"); no direct o finish commita.")
    if task.get("status") not in SHIPPABLE_STATUSES:
        _refuse(f"{task['id']} esta em '{task.get('status')}'.")
    delivery = config.get("delivery") or {}
    base = delivery.get("baseBranch") or DELIVERY_BASE_BRANCH_DEFAULT
    branch = current_branch()
    if not branch or branch == base:
        _refuse(f"rode de dentro do worktree da demanda (branch atual: {branch or 'nenhuma'}).")
    root = work_root(cwd)
    dirty = git_output(root, "status", "--porcelain")
    if dirty:
        _refuse("ha mudanca nao commitada no worktree - o PR mostraria outra coisa:\n" + dirty)
    if (delivery.get("pr") or {}).get("requestToTest", True) and not task.get("requestToTest"):
        _refuse('sem tabela Pedido -> Teste: registre com `ready --request-test "pedido :: teste"`.')
    settings = changelog_settings(config)
    if settings["style"] == "fragments" and not args.no_changelog:
        if not list((root / settings["dir"]).glob(f"{task['id']}.*.md")):
            _refuse(
                f"sem fragmento de changelog para {task['id']}: `guia changelog add`, "
                'ou --no-changelog "<motivo>" para mudanca so interna.'
            )
    _check_gate(root, list((delivery.get("gate") or {}).get("full") or []))
    message = compose_commit_message(task, args.unlock_reason, args.body, args.subject or task.get("commitSubject"))
    return {"root": root, "base": base, "branch": branch, "message": message, "delivery": delivery}


def ship(task: dict[str, Any], config: dict[str, Any], args: Any, cwd: Path | None = None) -> dict[str, Any]:
    context = preflight(task, config, args, cwd or Path.cwd())
    root, branch = context["root"], context["branch"]
    push = subprocess.run(["git", "push", "-u", "origin", branch], cwd=root, text=True, capture_output=True)
    if push.returncode != 0:
        _refuse(f"push falhou: {(push.stderr or push.stdout).strip()}")
    title = context["message"].splitlines()[0]
    footer = (context["delivery"].get("pr") or {}).get("footer")
    body = build_pr_body(task, args.body, args.no_changelog, footer)
    pr = gh_pr_upsert(root, context["base"], branch, title, body)
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    (QUEUE_DIR / f"{task['id']}.msg").write_text(context["message"] + "\n", encoding="utf-8", newline="\n")
    task["status"] = STATUS_IN_PR
    task["pr"] = {
        "number": pr["number"],
        "url": pr["url"],
        "branch": branch,
        "head": git_output(root, "rev-parse", "HEAD"),
        "shippedAt": now_iso(),
    }
    return task["pr"]


__all__ = ["QUEUE_DIR", "build_pr_body", "parse_request_test", "ship"]
