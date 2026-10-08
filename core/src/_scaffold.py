"""Andaimes de entrega gerados de core/templates/scaffold/ (D-120, R2 + R11).

Gera por pedido e nunca sobrescreve. `auditoria`, `pr-template` e
`dependabot` sao arquivos novos e autossuficientes; `ci-ok` e `protection`
so imprimem - o job agregador depende dos jobs do workflow do projeto, e
mudar a protecao do GitHub e acao externa do dono.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _constants import COMMIT_FORMAT_GITMOJI, DELIVERY_BASE_BRANCH_DEFAULT, PROCESS_FILE
from _delivery_facts import collect_facts, pull_request_jobs
from _git_ops import git_output
from _state import read_json

SCAFFOLD_DIR = "scaffold"
AUDIT_CONTEXT_DEFAULT = "Auditoria registrada"
CI_AGGREGATOR_DEFAULT = "CI ok"

# alvo -> (modelo, destino relativo ao repo, outros nomes que contam como existente)
FILE_TARGETS: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "auditoria": ("auditoria.yml", ".github/workflows/auditoria.yml", ()),
    "pr-template": (
        "pull_request_template.md",
        ".github/pull_request_template.md",
        (".github/PULL_REQUEST_TEMPLATE.md", "docs/pull_request_template.md", "pull_request_template.md"),
    ),
    "dependabot": ("dependabot.yml", ".github/dependabot.yml", (".github/dependabot.yaml",)),
}
PRINT_TARGETS = ("ci-ok", "protection")
TARGETS = (*FILE_TARGETS, *PRINT_TARGETS)


def _fact(facts: list[dict[str, Any]], name: str) -> Any:
    return next((fact.get("value") for fact in facts if fact["name"] == name), None)


def _settings(facts: list[dict[str, Any]]) -> dict[str, str]:
    delivery = read_json(PROCESS_FILE, {}).get("delivery") or {}
    workflow = _fact(facts, "audit-workflow") or {}
    commit_format = (delivery.get("commit") or {}).get("format")
    configured_context = (delivery.get("audit") or {}).get("statusContext")
    return {
        "audited": "yes" if (workflow or configured_context) else "",
        "baseBranch": delivery.get("baseBranch") or DELIVERY_BASE_BRANCH_DEFAULT,
        "statusContext": configured_context
        or workflow.get("statusContext")
        or AUDIT_CONTEXT_DEFAULT,
        "commitPrefix": "🧹 chore" if commit_format == COMMIT_FORMAT_GITMOJI else "chore",
        "aggregator": _fact(facts, "ci-aggregator") or CI_AGGREGATOR_DEFAULT,
    }


def _render(template: Path, settings: dict[str, str], needs: str = "") -> str:
    text = template.read_text(encoding="utf-8")
    replacements = {
        "__BASE_BRANCH__": settings["baseBranch"],
        "__STATUS_CONTEXT__": settings["statusContext"],
        "__COMMIT_PREFIX__": settings["commitPrefix"],
        "__NEEDS__": needs,
    }
    for token, value in replacements.items():
        text = text.replace(token, value)
    return text


def _existing(root: Path, destination: str, aliases: tuple[str, ...]) -> Path | None:
    for rel in (destination, *aliases):
        candidate = root / rel
        if candidate.exists():
            return candidate
    return None


def _protection_commands(slug: str, settings: dict[str, str], audited: bool) -> str:
    checks = [settings["aggregator"], *([settings["statusContext"]] if audited else [])]
    body = {
        "required_status_checks": {"strict": True, "contexts": checks},
        "enforce_admins": True,
        "required_pull_request_reviews": {"required_approving_review_count": 0},
        "restrictions": None,
        "required_linear_history": True,
        "allow_force_pushes": False,
        "allow_deletions": False,
    }
    base = settings["baseBranch"]
    return "\n".join([
        "# Proteção da base (ação externa: rode você, ou autorize). Nada foi aplicado.",
        "# 1. Só squash, apaga a branch no merge, sem auto-merge:",
        f"gh api -X PATCH repos/{slug} -F allow_squash_merge=true -F allow_merge_commit=false "
        "-F allow_rebase_merge=false -F delete_branch_on_merge=true -F allow_auto_merge=false",
        "# 2. Salve o JSON abaixo como protecao.json e aplique:",
        f"gh api -X PUT repos/{slug}/branches/{base}/protection --input protecao.json",
        "# Acrescente aos contexts os outros checks que devem barrar o merge (ex.: lock-check).",
        json.dumps(body, ensure_ascii=False, indent=2),
    ])


def _ci_ok_snippet(root: Path, folder: Path, settings: dict[str, str]) -> str:
    """Job agregador para o workflow principal de PR.

    Principal = o que ja tem o agregador; senao, o de mais jobs.
    """
    all_jobs = pull_request_jobs(root)
    by_file = {name: [job for job in jobs if job != "ci-ok"] for name, jobs in all_jobs.items()}
    main = max(by_file, key=lambda name: ("ci-ok" in all_jobs[name], len(by_file[name])), default=None)
    jobs = by_file.get(main) or ["<seus-jobs>"]
    header = [f"# Cole este job em {main or 'seu workflow de pull_request'} (dentro de `jobs:`)."]
    others = {name: found for name, found in by_file.items() if name != main and found}
    if others:
        header.append("# Jobs de outros workflows nao entram no `needs` (ele so ve o proprio arquivo);")
        header.append("# exija-os direto na protecao da base:")
        header += [f"#   {name}: {', '.join(found)}" for name, found in others.items()]
    return "\n".join(header) + "\n" + _render(folder / "ci-ok-job.yml", settings, ", ".join(jobs))


def scaffold(target: str, templates_dir: Path, cwd: Path | None = None) -> tuple[int, str]:
    """(codigo de saida, texto para imprimir)."""
    cwd = cwd or Path.cwd()
    toplevel = git_output(cwd, "rev-parse", "--show-toplevel")
    root = Path(toplevel) if toplevel else cwd
    facts = collect_facts(cwd)
    settings = _settings(facts)
    folder = templates_dir / SCAFFOLD_DIR

    if target in FILE_TARGETS:
        template, destination, aliases = FILE_TARGETS[target]
        found = _existing(root, destination, aliases)
        if found is not None:
            return 1, f"{found.relative_to(root).as_posix()} ja existe: nada gravado (o andaime nunca sobrescreve)."
        path = root / destination
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_render(folder / template, settings), encoding="utf-8", newline="\n")
        return 0, f"+ {destination}"

    if target == "ci-ok":
        return 0, _ci_ok_snippet(root, folder, settings)

    slug = _fact(facts, "remote")
    if not slug:
        return 1, "Sem remoto GitHub: nao ha protecao a configurar."
    return 0, _protection_commands(slug, settings, audited=bool(settings["audited"]))


__all__ = ["TARGETS", "scaffold"]
