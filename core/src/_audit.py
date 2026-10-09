"""`guia audit`: registrar a auditoria do PR da demanda (D-123, R4/R12).

O motor nao audita - quem audita e a skill de `skills.audit` (padrao
`pr-audit`) ou, sem ela, o agente pelo checklist embutido do Guia: a
auditoria e um portao e nao vira aprovacao por falta de skill. O motor mostra
o que auditar (head, patch-id), comenta o relatorio no PR e, aprovado, fecha
com o marcador do head que o `auditoria.yml` transforma em status.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from _changelog import work_root
from _clock import now_iso
from _constants import DELIVERY_BASE_BRANCH_DEFAULT
from _git_ops import current_branch, git_output
from _github import gh_pr_comment

AUDIT_CHECKLIST = "audit-checklist.md"
RESULT_APPROVED = "approved"
RESULT_REJECTED = "rejected"


def marker(sha: str) -> str:
    return f"<!-- auditoria-aprovada sha={sha} -->"


def patch_id(root: Path, base_ref: str, head: str = "HEAD") -> str | None:
    """`git diff <merge-base>..<head> | git patch-id --verbatim` (R8).

    Igual entre dois heads = mesmo conteudo de PR, mesmo apos rebase limpo.
    `--verbatim`, nao `--stable`: o padrao descarta espaco em branco, e mudar
    so a indentacao de um bloco Python (que muda o comportamento) daria o
    mesmo id - o executor carregaria a auditoria sobre codigo diferente.
    """
    base = git_output(root, "merge-base", head, base_ref)
    if not base:
        return None
    diff = subprocess.run(["git", "diff", f"{base}..{head}"], cwd=root, capture_output=True)
    if diff.returncode != 0 or not diff.stdout:
        return None
    result = subprocess.run(["git", "patch-id", "--verbatim"], cwd=root, input=diff.stdout, capture_output=True)
    output = result.stdout.decode("ascii", errors="replace").split()
    return output[0] if output else None


def audit_target(config: dict[str, Any], cwd: Path | None = None) -> dict[str, Any]:
    """Head local, head no remoto e patch-id - o que esta sendo auditado."""
    root = work_root(cwd)
    base = (config.get("delivery") or {}).get("baseBranch") or DELIVERY_BASE_BRANCH_DEFAULT
    branch = current_branch()
    remote = git_output(root, "ls-remote", "origin", f"refs/heads/{branch}") if branch else None
    return {
        "root": root,
        "branch": branch,
        "head": git_output(root, "rev-parse", "HEAD"),
        "remoteHead": remote.split()[0] if remote else None,
        "patchId": patch_id(root, f"origin/{base}"),
        # D-140: a base auditada - sem ela nao ha range-diff depois do rebase.
        "base": git_output(root, "merge-base", "HEAD", f"origin/{base}"),
    }


def delta_range(root: Path, previous: dict[str, Any] | None, target: dict[str, Any]) -> str | None:
    """R8 (D-140): head novo depois de uma auditoria aprovada -> so o que mudou.

    Devolve os dois intervalos do `git range-diff <base-velha>..<head-velho>
    <base-nova>..<head-novo>`, ou None quando falta qualquer peca (auditoria
    anterior nao aprovada, base nao gravada, commit antigo fora do repositorio
    local): ai a auditoria e do diff inteiro, o lado seguro.
    """
    if not previous or previous.get("result") != RESULT_APPROVED:
        return None
    old_head, old_base, head, base = previous.get("auditedSha"), previous.get("auditedBase"), target["head"], target.get("base")
    if not (old_head and old_base and head and base) or old_head == head:
        return None
    if any(git_output(root, "cat-file", "-e", f"{sha}^{{commit}}") is None for sha in (old_head, old_base)):
        return None
    return f"{old_base}..{old_head} {base}..{head}"


def record_audit(task: dict[str, Any], target: dict[str, Any], report: str, approve: bool, via: str) -> dict[str, Any]:
    """Comenta o relatorio no PR; aprovado, com o marcador do head."""
    pr = task.get("pr") or {}
    if not pr.get("number"):
        raise SystemExit(f"{task['id']} sem PR registrado: rode `guia ship` antes.")
    if not report.strip():
        raise SystemExit("Relatorio vazio: a auditoria precisa de achados e recomendacao.")
    if not target["head"] or target["head"] != target["remoteHead"]:
        raise SystemExit(
            f"O head local ({target['head']}) nao e o do remoto ({target['remoteHead']}): o marcador "
            "tem de apontar o commit que o GitHub ve. Rode `guia ship` (ou push) e audite de novo."
        )
    previous = task.get("audit")
    delta = delta_range(target["root"], previous, target)
    body = report.rstrip() + "\n"
    if delta:
        body = f"Auditoria de delta desde {previous['auditedSha'][:12]}: `git range-diff {delta}`\n\n" + body
    if approve:
        body += "\n" + marker(target["head"]) + "\n"
    gh_pr_comment(target["root"], pr["number"], body)
    task["audit"] = {
        "result": RESULT_APPROVED if approve else RESULT_REJECTED,
        "auditedSha": target["head"],
        "auditedBase": target.get("base"),
        "auditedPatchId": target["patchId"],
        "mode": "delta" if delta else "full",
        "via": via,
        "at": now_iso(),
    }
    if delta:
        task["audit"].update(deltaFrom=previous["auditedSha"], range=delta)
    return task["audit"]


__all__ = ["AUDIT_CHECKLIST", "audit_target", "delta_range", "marker", "patch_id", "record_audit"]
