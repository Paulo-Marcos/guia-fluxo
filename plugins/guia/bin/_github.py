"""Adaptador fino do GitHub (D-117, R2).

Unico lugar do motor que fala com o GitHub, via `gh` (sem token proprio,
sem dependencia nova). So leitura. Nos testes, `GUIA_GH_FIXTURE` aponta um
JSON com as respostas: chave = endpoint do `gh api`, valor = resposta; a
chave `__auth__` responde ao `gh auth status`. Endpoint ausente no fixture =
404. Mesmo espirito do `GUIA_NOW` (seam explicito, nunca ligado por padrao).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

FIXTURE_ENV = "GUIA_GH_FIXTURE"
_REMOTE_RE = re.compile(r"github\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?/?$")


def _fixture() -> dict[str, Any] | None:
    path = os.environ.get(FIXTURE_ENV)
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def repo_slug(cwd: Path) -> str | None:
    """`dono/repo` do remoto `origin`, quando ele e do GitHub."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"], cwd=cwd, text=True, capture_output=True
        )
    except (FileNotFoundError, OSError):
        return None
    match = _REMOTE_RE.search(result.stdout.strip()) if result.returncode == 0 else None
    return f"{match.group(1)}/{match.group(2)}" if match else None


def gh_status() -> str:
    """`autenticado`, `nao autenticado` ou `gh ausente`."""
    fixture = _fixture()
    if fixture is not None:
        return "autenticado" if fixture.get("__auth__") else "nao autenticado"
    if shutil.which("gh") is None:
        return "gh ausente"
    result = subprocess.run(["gh", "auth", "status"], text=True, capture_output=True)
    return "autenticado" if result.returncode == 0 else "nao autenticado"


def gh_api(endpoint: str) -> tuple[Any | None, str | None]:
    """(resposta, erro) de `gh api <endpoint>`. 404 vira (None, "nao encontrado")."""
    fixture = _fixture()
    if fixture is not None:
        if endpoint in fixture:
            return fixture[endpoint], None
        return None, "nao encontrado"
    if shutil.which("gh") is None:
        return None, "gh ausente"
    result = subprocess.run(["gh", "api", endpoint], text=True, encoding="utf-8", capture_output=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        return None, "nao encontrado" if "404" in detail else (detail.splitlines() or ["erro"])[0]
    try:
        return json.loads(result.stdout), None
    except ValueError:
        return None, "resposta nao e JSON"


def _fixture_prs_path() -> Path | None:
    path = os.environ.get(FIXTURE_ENV)
    return Path(path + ".prs.json") if path else None


def _fixture_prs() -> list[dict[str, Any]]:
    path = _fixture_prs_path()
    return json.loads(path.read_text(encoding="utf-8")) if path and path.exists() else []


def gh_pr_find(cwd: Path, branch: str) -> dict[str, Any] | None:
    """PR aberto da `branch` ({number, url}) ou None."""
    if _fixture() is not None:
        return next((pr for pr in _fixture_prs() if pr.get("headRef") == branch), None)
    result = subprocess.run(
        ["gh", "pr", "view", branch, "--json", "number,url,state"],
        cwd=cwd, text=True, encoding="utf-8", capture_output=True,
    )
    if result.returncode != 0:
        return None
    data = json.loads(result.stdout)
    return data if data.get("state") == "OPEN" else None


def gh_pr_upsert(cwd: Path, base: str, branch: str, title: str, body: str) -> dict[str, Any]:
    """Abre o PR da `branch` ou atualiza titulo e corpo do que ja existe.

    Escrita no GitHub so por aqui. Corpo vai por arquivo (`--body-file`):
    nunca por argumento interpolado.
    """
    existing = gh_pr_find(cwd, branch)
    if _fixture() is not None:
        prs = _fixture_prs()
        if existing:
            for pr in prs:
                if pr["number"] == existing["number"]:
                    pr.update(title=title, body=body)
            result = existing
        else:
            result = {"number": len(prs) + 1, "url": f"https://example.invalid/pull/{len(prs) + 1}"}
            prs.append({**result, "headRef": branch, "base": base, "title": title, "body": body})
        _fixture_prs_path().write_text(json.dumps(prs, ensure_ascii=False), encoding="utf-8")
        return {"number": result["number"], "url": result["url"]}
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as handle:
        handle.write(body)
        body_file = handle.name
    try:
        if existing:
            command = ["gh", "pr", "edit", str(existing["number"]), "--title", title, "--body-file", body_file]
        else:
            command = ["gh", "pr", "create", "--base", base, "--head", branch, "--title", title, "--body-file", body_file]
        result = subprocess.run(command, cwd=cwd, text=True, encoding="utf-8", capture_output=True)
    finally:
        os.unlink(body_file)
    if result.returncode != 0:
        raise SystemExit(f"gh recusou o PR: {(result.stderr or result.stdout).strip()}")
    created = gh_pr_find(cwd, branch)
    if created is None:
        raise SystemExit("PR criado, mas `gh pr view` nao o encontrou.")
    return {"number": created["number"], "url": created["url"]}


def gh_pr_comment(cwd: Path, number: int, body: str) -> None:
    """Comenta no PR (corpo por arquivo, nunca por argumento)."""
    if _fixture() is not None:
        path = Path(os.environ[FIXTURE_ENV] + ".comments.json")
        comments = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        comments.append({"number": number, "body": body})
        path.write_text(json.dumps(comments, ensure_ascii=False), encoding="utf-8")
        return
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as handle:
        handle.write(body)
        body_file = handle.name
    try:
        result = subprocess.run(
            ["gh", "pr", "comment", str(number), "--body-file", body_file],
            cwd=cwd, text=True, encoding="utf-8", capture_output=True,
        )
    finally:
        os.unlink(body_file)
    if result.returncode != 0:
        raise SystemExit(f"gh recusou o comentario: {(result.stderr or result.stdout).strip()}")


def _save_fixture_prs(prs: list[dict[str, Any]]) -> None:
    _fixture_prs_path().write_text(json.dumps(prs, ensure_ascii=False), encoding="utf-8")


def _fixture_pr(number: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    prs = _fixture_prs()
    entry = next((pr for pr in prs if pr["number"] == number), None)
    if entry is None:
        raise SystemExit(f"PR #{number} nao existe no fixture.")
    return prs, entry


def _gh_json(cwd: Path, *args: str) -> Any:
    result = subprocess.run(["gh", *args], cwd=cwd, text=True, encoding="utf-8", capture_output=True)
    if result.returncode != 0:
        raise SystemExit(f"gh {' '.join(args[:3])} falhou: {(result.stderr or result.stdout).strip()}")
    return json.loads(result.stdout)


def gh_pr_state(cwd: Path, number: int) -> dict[str, Any]:
    """{state, head, mergeState} do PR (D-127)."""
    if _fixture() is not None:
        _prs, entry = _fixture_pr(number)
        return {"state": entry.get("state", "OPEN"), "head": entry.get("head"), "mergeState": entry.get("mergeState", "CLEAN")}
    data = _gh_json(cwd, "pr", "view", str(number), "--json", "state,headRefOid,mergeStateStatus")
    return {"state": data["state"], "head": data["headRefOid"], "mergeState": data["mergeStateStatus"]}


def gh_pr_update_branch(cwd: Path, number: int) -> tuple[str | None, str | None]:
    """Rebase da branch do PR na base: (head novo, erro)."""
    if _fixture() is not None:
        prs, entry = _fixture_pr(number)
        after = entry.get("afterUpdate") or {}
        if after.get("conflict"):
            return None, "conflito no rebase com a base"
        entry["head"] = after.get("head", entry.get("head"))
        entry["mergeState"] = "CLEAN"
        _save_fixture_prs(prs)
        return entry["head"], None
    result = subprocess.run(
        ["gh", "pr", "update-branch", str(number), "--rebase"],
        cwd=cwd, text=True, encoding="utf-8", capture_output=True,
    )
    if result.returncode != 0:
        return None, (result.stderr or result.stdout).strip() or "update-branch falhou"
    return gh_pr_state(cwd, number)["head"], None


def gh_pr_checks(cwd: Path, number: int, timeout_seconds: float, poll_seconds: float = 20.0) -> tuple[str, list[str]]:
    """Espera os checks exigidos: ("pass" | "fail" | "pending", checks que falharam)."""
    if _fixture() is not None:
        _prs, entry = _fixture_pr(number)
        return entry.get("checks", "pass"), list(entry.get("failing") or [])
    deadline = time.monotonic() + timeout_seconds
    while True:
        result = subprocess.run(
            ["gh", "pr", "checks", str(number), "--required", "--json", "name,bucket"],
            cwd=cwd, text=True, encoding="utf-8", capture_output=True,
        )
        checks = json.loads(result.stdout or "[]") if result.stdout.strip().startswith("[") else []
        failing = [c["name"] for c in checks if c.get("bucket") in ("fail", "cancel")]
        if failing:
            return "fail", failing
        if checks and all(c.get("bucket") in ("pass", "skipping") for c in checks):
            return "pass", []
        if time.monotonic() > deadline:
            return "pending", []
        time.sleep(poll_seconds)


def gh_pr_merge(cwd: Path, number: int, head: str, subject: str, body: str) -> str | None:
    """Squash preso ao head (`--match-head-commit`); devolve o erro ou None."""
    if _fixture() is not None:
        prs, entry = _fixture_pr(number)
        if entry.get("head") != head:
            return f"o head mudou ({entry.get('head')})"
        if entry.get("mergeState", "CLEAN") not in ("CLEAN", "HAS_HOOKS", "UNSTABLE"):
            return "the base branch policy prohibits the merge"
        entry["merged"] = {"matchHead": head, "subject": subject, "body": body}
        entry["mergeCommit"] = f"{number:040x}"
        entry["state"] = "MERGED"
        _save_fixture_prs(prs)
        return None
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as handle:
        handle.write(body)
        body_file = handle.name
    try:
        result = subprocess.run(
            ["gh", "pr", "merge", str(number), "--squash", "--match-head-commit", head,
             "--subject", subject, "--body-file", body_file],
            cwd=cwd, text=True, encoding="utf-8", capture_output=True,
        )
    finally:
        os.unlink(body_file)
    return None if result.returncode == 0 else (result.stderr or result.stdout).strip() or "merge falhou"


def gh_pr_merge_commit(cwd: Path, number: int) -> str | None:
    """SHA do commit de squash na base (D-128)."""
    if _fixture() is not None:
        _prs, entry = _fixture_pr(number)
        return entry.get("mergeCommit")
    data = _gh_json(cwd, "pr", "view", str(number), "--json", "mergeCommit")
    return (data.get("mergeCommit") or {}).get("oid")


def gh_commit_ci(cwd: Path, sha: str, timeout_seconds: float, poll_seconds: float = 30.0) -> tuple[str, list[str]]:
    """CI dos workflows no commit `sha` da base: ("pass" | "fail" | "pending", falhas).

    O CI do PR prova o PR; o da main prova a combinacao (D-128).
    """
    if _fixture() is not None:
        entry = next((pr for pr in _fixture_prs() if pr.get("mergeCommit") == sha), {})
        verdict = entry.get("mainCi", "pass")
        return verdict, (["ci da main"] if verdict == "fail" else [])
    deadline = time.monotonic() + timeout_seconds
    while True:
        result = subprocess.run(
            ["gh", "run", "list", "--commit", sha, "--json", "name,status,conclusion"],
            cwd=cwd, text=True, encoding="utf-8", capture_output=True,
        )
        runs = json.loads(result.stdout) if result.returncode == 0 and result.stdout.strip() else []
        done = [run for run in runs if run.get("status") == "completed"]
        failing = [run["name"] for run in done if run.get("conclusion") not in ("success", "skipped", "neutral")]
        if failing:
            return "fail", failing
        if runs and len(done) == len(runs):
            return "pass", []
        if time.monotonic() > deadline:
            return "pending", []
        time.sleep(poll_seconds)


def _fixture_closed_path() -> Path:
    return Path(os.environ[FIXTURE_ENV] + ".closed.json")


def gh_bot_prs(cwd: Path) -> list[dict[str, Any]]:
    """PRs abertos do Dependabot: numero, titulo, rotulos, arquivos e diff (D-129)."""
    fixture = _fixture()
    if fixture is not None:
        path = _fixture_closed_path()
        closed = {c["number"] for c in json.loads(path.read_text(encoding="utf-8"))} if path.exists() else set()
        return [pr for pr in fixture.get("__dependabot__", []) if pr["number"] not in closed]
    prs = _gh_json(cwd, "pr", "list", "--author", "app/dependabot", "--state", "open",
                   "--json", "number,title,labels,files")
    result = []
    for pr in prs:
        diff = subprocess.run(["gh", "pr", "diff", str(pr["number"])], cwd=cwd, text=True,
                              encoding="utf-8", errors="replace", capture_output=True)
        result.append({
            "number": pr["number"],
            "title": pr.get("title", ""),
            "labels": [label.get("name", "") for label in pr.get("labels") or []],
            "files": [f.get("path", "") for f in pr.get("files") or []],
            "diff": diff.stdout if diff.returncode == 0 else "",
        })
    return result


def gh_labeled_prs(cwd: Path, label: str) -> list[dict[str, Any]]:
    """PRs abertos com o rotulo `label`: numero, titulo, branch e head (D-130)."""
    fixture = _fixture()
    if fixture is not None:
        return list(fixture.get("__labeled__", []))
    return _gh_json(cwd, "pr", "list", "--label", label, "--state", "open",
                    "--json", "number,title,headRefName,headRefOid")


def gh_pr_close(cwd: Path, number: int, comment: str) -> None:
    """Fecha o PR com um comentario (D-129: PR do bot incorporado ao lote)."""
    if _fixture() is not None:
        path = _fixture_closed_path()
        closed = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        closed.append({"number": number, "comment": comment})
        path.write_text(json.dumps(closed, ensure_ascii=False), encoding="utf-8")
        return
    state = _gh_json(cwd, "pr", "view", str(number), "--json", "state")
    if state.get("state") != "OPEN":
        return
    subprocess.run(["gh", "pr", "close", str(number), "--comment", comment],
                   cwd=cwd, text=True, encoding="utf-8", capture_output=True)


def pr_patch_id(cwd: Path, number: int, head: str, base_branch: str) -> str | None:
    """Patch-id do PR no `head` (R8): igual = mesmo conteudo, mesmo apos rebase."""
    if _fixture() is not None:
        _prs, entry = _fixture_pr(number)
        return (entry.get("patchIds") or {}).get(head)
    from _audit import patch_id  # import tardio: _audit importa este modulo

    subprocess.run(["git", "fetch", "-q", "origin", base_branch, f"refs/pull/{number}/head"], cwd=cwd, capture_output=True)
    return patch_id(cwd, f"origin/{base_branch}", head)


__all__ = [
    "FIXTURE_ENV",
    "gh_api",
    "gh_bot_prs",
    "gh_commit_ci",
    "gh_labeled_prs",
    "gh_pr_checks",
    "gh_pr_close",
    "gh_pr_comment",
    "gh_pr_find",
    "gh_pr_merge",
    "gh_pr_merge_commit",
    "gh_pr_state",
    "gh_pr_update_branch",
    "gh_pr_upsert",
    "gh_status",
    "pr_patch_id",
    "repo_slug",
]
