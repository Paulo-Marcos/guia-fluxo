"""Os PRs do Dependabot no executor (D-129, R11).

Juntar versoes, rodar o portao no conjunto e julgar compatibilidade e
trabalho de juizo - da skill `pr-bump`, no chat. O motor faz a mecanica:
inventaria e tria os PRs do bot, cria a demanda do lote (uma so por vez) e,
depois do merge do lote, fecha cada PR incorporado com link para ele. PR do
bot nunca entra na fila normal nem recebe update-branch: seria CI jogado
fora num PR que vai ser substituido.
"""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import Any

from _constants import KIND_CHORE, ROOT, STATUS_PLANNED, TASKS_FILE
from _features_md import upsert_features_entry
from _github import gh_bot_prs, gh_pr_close
from _state import read_json, write_json
from _tasks import next_task_id, new_task

LOTE_TITLE = "Atualizar as dependências do Dependabot em lote"
TRIGGER_ON_IDLE = "on-idle"
# Manifestos e lockfiles: mexer so neles e bump.
DEPENDENCY_FILES = (
    "requirements*.txt", "*.lock", "package.json", "package-lock.json", "pnpm-lock.yaml",
    "yarn.lock", "pyproject.toml", "go.mod", "go.sum", "Cargo.toml", "Gemfile", "Gemfile.lock",
)
_USES_LINE = re.compile(r"^\s*-?\s*uses:\s*\S+")
_CLOSED_STATUSES = frozenset({"Integrada", "Validada", "Finalizada", "Cancelada"})


def _workflow_change_is_only_uses(diff: str, path: str) -> bool:
    """No arquivo `path` do diff, toda linha mudada e uma linha `uses:`."""
    in_file = False
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            in_file = line.endswith(f" b/{path}")
            continue
        if not in_file or line.startswith(("+++", "---")):
            continue
        if line.startswith(("+", "-")) and not _USES_LINE.match(line[1:]):
            return False
    return True


def _classify(pr: dict[str, Any]) -> dict[str, Any]:
    reasons = []
    for path in pr.get("files") or []:
        name = Path(path).name
        if path.startswith(".github/workflows/"):
            if not _workflow_change_is_only_uses(pr.get("diff") or "", path):
                reasons.append(f"{path} muda mais que as linhas uses:")
        elif not any(fnmatch.fnmatch(name, pattern) for pattern in DEPENDENCY_FILES):
            reasons.append(f"{path} nao e manifesto nem lockfile")
    labels = [str(label).lower() for label in pr.get("labels") or []]
    return {
        "number": pr["number"],
        "title": pr.get("title", ""),
        "bump": not reasons,
        "security": "security" in labels,
        "reason": "; ".join(reasons) or None,
    }


def triage(prs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_classify(pr) for pr in prs]


def inventory() -> dict[str, Any]:
    triaged = triage(gh_bot_prs(ROOT))
    bumps = [t for t in triaged if t["bump"]]
    return {
        "bumps": bumps,
        "others": [t for t in triaged if not t["bump"]],
        "security": any(t["security"] for t in bumps),
    }


def open_lote() -> dict[str, Any] | None:
    tasks = read_json(TASKS_FILE, {"tasks": []}).get("tasks", [])
    return next((t for t in tasks if t.get("dependabot") and t.get("status") not in _CLOSED_STATUSES), None)


def create_lote(inv: dict[str, Any]) -> dict[str, Any] | None:
    """Cria a demanda do lote (Planejada: quem a executa e um chat com a pr-bump)."""
    if not inv["bumps"] or open_lote():
        return None
    data = read_json(TASKS_FILE, {"schemaVersion": 1, "tasks": []})
    numbers = [b["number"] for b in inv["bumps"]]
    context = (
        "Lote dos PRs do Dependabot " + ", ".join(f"#{n}" for n in numbers)
        + ": rode a skill pr-bump num chat (junta tudo, piso de supply-chain, portao uma vez), "
        "um PR so com `Closes #N` de cada um."
        + (" Inclui atualizacao de SEGURANCA: prioridade hotfix na fila." if inv["security"] else "")
    )
    task = new_task(next_task_id(KIND_CHORE, data.get("tasks", [])), KIND_CHORE, LOTE_TITLE, context,
                    "Dependabot (executor do Guia)", status=STATUS_PLANNED)
    task["dependabot"] = {"prs": numbers, "security": inv["security"]}
    data.setdefault("tasks", []).insert(0, task)
    write_json(TASKS_FILE, data)
    upsert_features_entry(task)
    return task


def on_idle(config: dict[str, Any]) -> dict[str, Any] | None:
    """Fila vazia e trigger on-idle: cria o lote se houver bumps e nenhum lote aberto."""
    trigger = ((config.get("delivery") or {}).get("dependencies") or {}).get("trigger", TRIGGER_ON_IDLE)
    if trigger != TRIGGER_ON_IDLE:
        return None
    return create_lote(inventory())


def close_incorporated(task: dict[str, Any]) -> list[int]:
    """Depois do merge do lote, fecha cada PR do bot incorporado com o link."""
    lote = task.get("dependabot") or {}
    pr = (task.get("pr") or {}).get("number")
    closed = []
    for number in lote.get("prs") or []:
        gh_pr_close(ROOT, number, f"Incorporado ao lote do Dependabot, PR #{pr} ({task['id']}).")
        closed.append(number)
    return closed


__all__ = ["LOTE_TITLE", "close_incorporated", "create_lote", "inventory", "on_idle", "open_lote", "triage"]
