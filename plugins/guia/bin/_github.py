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
        return next((pr for pr in _fixture_prs() if pr["head"] == branch), None)
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
            prs.append({**result, "head": branch, "base": base, "title": title, "body": body})
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


__all__ = ["FIXTURE_ENV", "gh_api", "gh_pr_find", "gh_pr_upsert", "gh_status", "repo_slug"]
