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


__all__ = ["FIXTURE_ENV", "gh_api", "gh_status", "repo_slug"]
