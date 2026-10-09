"""PRs da nuvem para a fila pelo rotulo `guia:fila` (D-130, R5 Nuvem).

A sessao na nuvem nao alcanca o `.guia/` do PC: ela abre o PR e poe o
rotulo. Aqui o PR entra na fila SEM auditoria - a demanda e achada pela
branch `d-NNN-*` (a demanda nasce no Guia antes; o prompt da nuvem leva o id).
Sem auditoria nada integra: quem audita e o PC, onde moram as skills.
"""

from __future__ import annotations

from typing import Any

from _clock import now_iso
from _constants import ROOT, STATUS_IN_QUEUE
from _github import gh_labeled_prs
from _merge_queue import PRIORITY_NORMAL, STATE_WAITING, find, mutate
from _tasks import BRANCH_TASK_RE, find_task, save_task

CLOUD_LABEL = "guia:fila"


def _task_for_branch(branch: str) -> dict[str, Any] | None:
    match = BRANCH_TASK_RE.match(branch or "")
    return find_task(f"{match.group(1).upper()}-{match.group(2)}") if match else None


def import_labeled() -> tuple[list[str], list[str]]:
    """(ids importados, avisos). Idempotente: item ja na fila nao duplica."""
    imported: list[str] = []
    warnings: list[str] = []
    for pr in gh_labeled_prs(ROOT, CLOUD_LABEL):
        task = _task_for_branch(pr["headRefName"])
        if task is None:
            warnings.append(
                f"PR #{pr['number']} ({pr['headRefName']}) tem o rotulo {CLOUD_LABEL}, mas a branch nao e de "
                "uma demanda conhecida (d-NNN-*): crie a demanda no PC e renomeie a branch."
            )
            continue

        def add(data: dict[str, Any], task: dict[str, Any] = task, pr: dict[str, Any] = pr) -> bool:
            if find(data, task["id"]):
                return False
            data["items"].append({
                "id": task["id"],
                "kind": task.get("kind"),
                "pr": pr["number"],
                "branch": pr["headRefName"],
                "head": pr["headRefOid"],
                "worktree": None,
                "enqueuedAt": now_iso(),
                "enqueuedBy": "cloud-label",
                "priority": PRIORITY_NORMAL,
                "dependsOn": list(task.get("dependsOn") or []),
                "auditedSha": None,
                "auditedPatchId": None,
                "approval": None,
                "mergeMessageFile": f".guia/queue/{task['id']}.msg",
                "state": STATE_WAITING,
                "attempts": 0,
                "log": [{"at": now_iso(), "msg": f"importado pelo rotulo {CLOUD_LABEL}"}],
            })
            return True

        if not mutate(add):
            continue
        task["pr"] = {**(task.get("pr") or {}), "number": pr["number"], "branch": pr["headRefName"], "head": pr["headRefOid"]}
        task["status"] = STATUS_IN_QUEUE
        save_task(task)
        imported.append(task["id"])
    return imported, warnings


__all__ = ["CLOUD_LABEL", "import_labeled"]
