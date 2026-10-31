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

import _locks
from _autonomy import LEVELS, rank, settings as autonomy_settings
from _clock import now_iso
from _constants import KIND_CHORE, ROOT, STATUS_PLANNED, TASKS_FILE
from _features_md import upsert_features_entry
from _git_ops import git_output
from _github import gh_bot_prs, gh_pr_close
from _state import read_json
from _tasks import edit_tasks, next_task_id, new_task

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


def _is_dependency_file(path: str) -> bool:
    return any(fnmatch.fnmatch(Path(path).name, pattern) for pattern in DEPENDENCY_FILES)


def _version_only(status: str, path: str, diff: str, fragment_prefix: str) -> bool:
    """O arquivo e so versao: manifesto/lockfile modificado, workflow so com `uses:`, ou o fragmento do lote."""
    if status == "A" and path.startswith(fragment_prefix) and path.endswith(".md"):
        return True
    if status != "M":
        return False  # lockfile novo, arquivo apagado ou renomeado: decisao do dono
    if path.startswith(".github/workflows/"):
        return _workflow_change_is_only_uses(diff, path)
    return _is_dependency_file(path)


def lote_human_reasons(task: dict[str, Any], base: str, branch: str | None, config: dict[str, Any]) -> list[str]:
    """No pilot (D-150): por que o lote precisa do dono - vazio = so versao, segue sozinho.

    Arquivo por arquivo, pelo git (nunca pela lista declarada): manifesto ou
    lockfile modificado, workflow em que toda linha mudada e `uses:` e o
    fragmento de changelog do proprio lote seguem. Qualquer outro arquivo -
    codigo, linha de base de catraca, lockfile novo - para no dono. Trava
    tocada tambem para (o dono pode ter travado o proprio requirements.txt);
    so a adicao do fragmento do lote nao conta.
    """
    if not branch:
        return ["caminhos do PR nao conferidos pelo git"]
    git_output(ROOT, "fetch", "-q", "origin", base, branch)
    span = f"origin/{base}...origin/{branch}"
    names = git_output(ROOT, "diff", "--name-status", "--no-renames", span)
    if names is None:
        return ["caminhos do PR nao conferidos pelo git"]
    diff = git_output(ROOT, "diff", span, "--", ".github/workflows") or ""
    fragment_prefix = f"{(((config.get('delivery') or {}).get('changelog') or {}).get('dir') or 'changelog.d')}/{task['id']}."
    entries = [line.split("\t", 1) for line in names.splitlines() if "\t" in line]
    beyond = [path for status, path in entries if not _version_only(status[0], path, diff, fragment_prefix)]
    reasons = [f"o lote mexe alem de versao: {', '.join(beyond)}"] if beyond else []
    lines = [f"{status}\t{path}" for status, path in entries if not path.startswith(fragment_prefix)]
    blocked = sorted({m.lock["id"] for m in _locks.lock_api.find_blocked(_locks.lock_api.events_from_name_status(lines))})
    if blocked:
        reasons.append("toca trava: " + ", ".join(blocked))
    return reasons


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
    return _open_in(read_json(TASKS_FILE, {"tasks": []}).get("tasks", []))


def _open_in(tasks: list[dict[str, Any]]) -> dict[str, Any] | None:
    return next((t for t in tasks if t.get("dependabot") and t.get("status") not in _CLOSED_STATUSES), None)


def lote_level(config: dict[str, Any]) -> str | None:
    """Nivel de autonomia dos lotes novos (D-149): `delivery.dependencies.autonomy`, limitado pelo teto.

    None = o lote segue o `autonomy.default` como qualquer demanda.
    """
    wanted = (((config.get("delivery") or {}).get("dependencies") or {}).get("autonomy"))
    if wanted not in LEVELS:
        return None
    ceiling = autonomy_settings(config)["ceiling"]
    return LEVELS[min(rank(wanted), rank(ceiling))]


def create_lote(inv: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Cria a demanda do lote (Planejada: quem a executa e um chat com a skill da etapa deps)."""
    if not inv["bumps"]:
        return None
    numbers = [b["number"] for b in inv["bumps"]]
    context = (
        "Lote dos PRs do Dependabot " + ", ".join(f"#{n}" for n in numbers)
        + ": `/guia:deps --now` conduz o lote (skill da etapa deps, padrao pr-bump: junta tudo, piso de "
        "supply-chain, portao uma vez), um PR so com `Closes #N` de cada um."
        + (" Inclui atualizacao de SEGURANCA: prioridade hotfix na fila." if inv["security"] else "")
    )
    level = lote_level(config or {})

    def add(data: dict[str, Any]) -> dict[str, Any] | None:
        # Conferir "ja ha lote aberto" e gravar sob a mesma trava (D-208): duas
        # leituras seguidas deixavam dois executores criarem dois lotes.
        if _open_in(data.get("tasks", [])):
            return None
        task = new_task(next_task_id(KIND_CHORE, data.get("tasks", [])), KIND_CHORE, LOTE_TITLE, context,
                        "Dependabot (executor do Guia)", status=STATUS_PLANNED)
        task["dependabot"] = {"prs": numbers, "security": inv["security"]}
        if level:
            # Nivel dado pela configuracao do dono (o configurador), nao pelo agente.
            task["autonomy"] = {"level": level, "setBy": "config", "at": now_iso()}
        data.setdefault("tasks", []).insert(0, task)
        return task

    task = edit_tasks(add)
    if task is None:
        return None
    upsert_features_entry(task)
    return task


def on_idle(config: dict[str, Any]) -> dict[str, Any] | None:
    """Fila vazia e trigger on-idle: cria o lote se houver bumps e nenhum lote aberto."""
    trigger = ((config.get("delivery") or {}).get("dependencies") or {}).get("trigger", TRIGGER_ON_IDLE)
    if trigger != TRIGGER_ON_IDLE:
        return None
    return create_lote(inventory(), config)


def close_incorporated(task: dict[str, Any]) -> list[int]:
    """Depois do merge do lote, fecha cada PR do bot incorporado com o link."""
    lote = task.get("dependabot") or {}
    pr = (task.get("pr") or {}).get("number")
    closed = []
    for number in lote.get("prs") or []:
        gh_pr_close(ROOT, number, f"Incorporado ao lote do Dependabot, PR #{pr} ({task['id']}).")
        closed.append(number)
    return closed


__all__ = ["LOTE_TITLE", "close_incorporated", "create_lote", "inventory", "lote_human_reasons", "lote_level", "on_idle", "open_lote", "triage"]
