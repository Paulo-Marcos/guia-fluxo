"""Fatos de entrega do projeto e do GitHub (D-117, R2), cada um com a fonte.

So leitura. Base do `doctor --delivery`: a deriva (D-118) e os perfis (D-119)
decidem em cima destes fatos. Fato que nao pode ser lido (sem `gh`, sem
remoto) vem com `value = None` e uma `note` dizendo o que falta - nunca falha.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from _constants import DELIVERY_BASE_BRANCH_DEFAULT, PROCESS_FILE
from _git_ops import git_output
from _github import gh_api, gh_status, repo_slug
from _hooks_check import hooks_path_warnings
from _state import read_json

_CONTEXT_RE = re.compile(r"""context["']?\s*[=:]\s*["']([^"'\n]+)["']""")


def _fact(name: str, value: Any, source: str, note: str | None = None) -> dict[str, Any]:
    fact: dict[str, Any] = {"name": name, "value": value, "source": source}
    if note:
        fact["note"] = note
    return fact


def _workflows(root: Path) -> list[Path]:
    folder = root / ".github" / "workflows"
    if not folder.is_dir():
        return []
    return sorted([*folder.glob("*.yml"), *folder.glob("*.yaml")])


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError:
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _triggers(workflow: dict[str, Any]) -> dict[str, Any]:
    # PyYAML le a chave `on:` como o booleano True (YAML 1.1).
    raw = workflow.get("on", workflow.get(True, {}))
    if isinstance(raw, str):
        return {raw: None}
    if isinstance(raw, list):
        return {item: None for item in raw}
    return raw if isinstance(raw, dict) else {}


def _github_facts(slug: str | None, base_branch: str) -> list[dict[str, Any]]:
    auth = gh_status()
    facts = [_fact("gh", auth, "gh auth status")]
    if slug is None or auth != "autenticado":
        why = "sem remoto GitHub" if slug is None else f"gh {auth}: rode `gh auth login`"
        facts.append(_fact("protection", None, "gh api .../protection", why))
        facts.append(_fact("merge", None, "gh api repos/{o}/{r}", why))
        return facts

    endpoint = f"repos/{slug}/branches/{base_branch}/protection"
    data, error = gh_api(endpoint)
    if data is None:
        facts.append(_fact("protection", None, f"gh api {endpoint}", f"sem protecao em {base_branch} ({error})"))
    else:
        checks = data.get("required_status_checks") or {}
        facts.append(_fact("protection", {
            "checks": list(checks.get("contexts") or []),
            "strict": bool(checks.get("strict")),
            "enforceAdmins": bool((data.get("enforce_admins") or {}).get("enabled")),
            "linearHistory": bool((data.get("required_linear_history") or {}).get("enabled")),
        }, f"gh api {endpoint}"))

    repo, error = gh_api(f"repos/{slug}")
    if repo is None:
        facts.append(_fact("merge", None, f"gh api repos/{slug}", error))
    else:
        methods = [name for key, name in (("allow_squash_merge", "squash"), ("allow_merge_commit", "merge"),
                                          ("allow_rebase_merge", "rebase")) if repo.get(key)]
        facts.append(_fact("merge", {
            "methods": methods,
            "autoMerge": bool(repo.get("allow_auto_merge")),
            "deleteBranchOnMerge": bool(repo.get("delete_branch_on_merge")),
        }, f"gh api repos/{slug}"))
    return facts


def _audit_workflow(root: Path) -> dict[str, Any]:
    for path in _workflows(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        if "issue_comment" in text and "statuses" in text:
            match = _CONTEXT_RE.search(text)
            value = {"file": path.relative_to(root).as_posix(), "statusContext": match.group(1) if match else None}
            return _fact("audit-workflow", value, value["file"])
    return _fact("audit-workflow", None, ".github/workflows/", "nenhum workflow de issue_comment que grave status")


def _ci_aggregator(root: Path) -> dict[str, Any]:
    for path in _workflows(root):
        jobs = _load_yaml(path).get("jobs") or {}
        for job_id, job in jobs.items():
            if not isinstance(job, dict):
                continue
            if "always()" in str(job.get("if", "")) and job.get("needs"):
                return _fact("ci-aggregator", job.get("name") or job_id, path.relative_to(root).as_posix())
    return _fact("ci-aggregator", None, ".github/workflows/", "nenhum job com if: always() e needs")


def _changelog(root: Path) -> dict[str, Any]:
    path = root / "CHANGELOG.md"
    if not path.is_file():
        return _fact("changelog", None, "CHANGELOG.md", "sem CHANGELOG.md")
    text = path.read_text(encoding="utf-8", errors="replace")
    fragments = next((d for d in ("changelog.d", ".changes") if (root / d).is_dir()), None)
    return _fact("changelog", {
        "unreleased": "## [Unreleased]" in text,
        "keepAChangelog": "keepachangelog" in text.lower().replace(" ", ""),
        "fragmentsDir": fragments,
    }, "CHANGELOG.md")


def _release(root: Path) -> dict[str, Any]:
    scripts = sorted(p.relative_to(root).as_posix() for p in (root / "bin").glob("release.*")) if (root / "bin").is_dir() else []
    tag_workflow = None
    for path in _workflows(root):
        push = _triggers(_load_yaml(path)).get("push")
        if isinstance(push, dict) and push.get("tags"):
            tag_workflow = path.relative_to(root).as_posix()
            break
    version_file = root / "VERSION"
    version = version_file.read_text(encoding="utf-8").strip() if version_file.is_file() else None
    return _fact("release", {"scripts": scripts, "tagWorkflow": tag_workflow, "version": version},
                 "bin/release.*, .github/workflows/ (push: tags), VERSION")


def collect_facts(cwd: Path | None = None) -> list[dict[str, Any]]:
    cwd = cwd or Path.cwd()
    toplevel = git_output(cwd, "rev-parse", "--show-toplevel")
    root = Path(toplevel) if toplevel else cwd
    delivery = read_json(PROCESS_FILE, {}).get("delivery") or {}
    base_branch = delivery.get("baseBranch") or DELIVERY_BASE_BRANCH_DEFAULT
    slug = repo_slug(cwd)
    facts = [_fact("remote", slug, "git remote get-url origin", None if slug else "sem remoto GitHub")]
    facts += _github_facts(slug, base_branch)
    facts += [_audit_workflow(root), _ci_aggregator(root), _changelog(root), _release(root)]
    facts.append(_fact("hooks", {
        "hooksPath": git_output(cwd, "config", "--get", "core.hooksPath"),
        "warnings": hooks_path_warnings(cwd),
    }, "git config --show-origin --get core.hooksPath (comum e config.worktree)"))
    return facts


def _render_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, dict):
        return ", ".join(f"{key}={_render_value(item)}" for key, item in value.items())
    if isinstance(value, list):
        return "[" + ", ".join(str(item) for item in value) + "]"
    return str(value)


def print_delivery_facts(
    facts: list[dict[str, Any]],
    drift: list[str] | None = None,
    profile: tuple[str, list[str]] | None = None,
    as_json: bool = False,
) -> None:
    drift = drift or []
    profile_data = {"name": profile[0], "reasons": profile[1]} if profile else None
    if as_json:
        print(json.dumps({"facts": facts, "drift": drift, "profile": profile_data}, ensure_ascii=False, indent=2))
        return
    print("=== doctor --delivery: fatos ===")
    for fact in facts:
        print(f"- {fact['name']}: {_render_value(fact['value'])}")
        print(f"    fonte: {fact['source']}")
        if fact.get("note"):
            print(f"    nota:  {fact['note']}")
    print("=== deriva (configuracao x GitHub) ===")
    if not drift:
        print("- nenhuma")
    for item in drift:
        print(f"- {item}")
    if profile_data:
        print(f"=== perfil proposto: {profile_data['name']} (aplicar: guia profile --apply) ===")
        for reason in profile_data["reasons"]:
            print(f"- {reason}")


__all__ = ["collect_facts", "print_delivery_facts"]
