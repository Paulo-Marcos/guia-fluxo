"""Portao completo (`delivery.gate.full`) com registro por tree (D-182).

O mesmo commit passava duas vezes pelo portao: uma antes do `ready`, outra
dentro do `ship` - meia hora cada neste repo. O que o portao julga e o
conteudo, nao o commit: um tree aprovado com os mesmos comandos continua
aprovado. Por isso cada passagem limpa grava `HEAD^{tree}` + a impressao dos
comandos em `.guia/gate-passed.json` (estado local, fora do git), e o `ship`
pula o que ja passou. Arvore suja nao grava: o tree do HEAD nao seria o que
rodou.
"""

from __future__ import annotations

import hashlib
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any

from _clock import now_iso
from _constants import GUIA_DIR
from _git_ops import git_output
from _state import read_json, write_json

GATE_FILE = GUIA_DIR / "gate-passed.json"
GATE_KEEP = 50
TAIL_LINES = 15


def gate_commands(config: dict[str, Any]) -> list[str]:
    return list(((config.get("delivery") or {}).get("gate") or {}).get("full") or [])


def _fingerprint(commands: list[str]) -> str:
    return hashlib.sha256("\n".join(commands).encode("utf-8")).hexdigest()[:16]


def clean_tree(root: Path) -> str | None:
    """`HEAD^{tree}` quando a arvore esta limpa; suja (ou sem HEAD), None."""
    if git_output(root, "status", "--porcelain"):
        return None
    return git_output(root, "rev-parse", "HEAD^{tree}") or None


def _key(root: Path, commands: list[str]) -> tuple[str, str] | None:
    """(tree, impressao dos comandos) que identifica uma passagem; sem tree limpo ou sem comandos, None."""
    tree = clean_tree(root)
    if not tree or not commands:
        return None
    return tree, _fingerprint(commands)


def passed_entry(root: Path, commands: list[str]) -> dict[str, Any] | None:
    """O registro de quando este tree passou por estes comandos, se passou."""
    key = _key(root, commands)
    if not key:
        return None
    entries = read_json(GATE_FILE, {}).get("passed") or []
    return next((e for e in entries if (e.get("tree"), e.get("gate")) == key), None)


def describe_pass(entry: dict[str, Any]) -> str:
    """A frase de quando o tree passou, comum ao `guia gate` e ao `ship`."""
    return f"portao ja passou neste tree em {entry.get('at')} (commit {str(entry.get('head'))[:12]})"


def record_pass(root: Path, commands: list[str]) -> bool:
    """Grava o tree aprovado; arvore suja nao grava (devolve False)."""
    key = _key(root, commands)
    if not key:
        return False
    tree, gate = key
    entries = [e for e in read_json(GATE_FILE, {}).get("passed") or [] if (e.get("tree"), e.get("gate")) != (tree, gate)]
    entries.append({"tree": tree, "gate": gate, "head": git_output(root, "rev-parse", "HEAD"), "at": now_iso()})
    write_json(GATE_FILE, {"passed": entries[-GATE_KEEP:]})
    return True


def run_gate(root: Path, commands: list[str]) -> str | None:
    """Roda cada comando em `root`; None se todos passaram, senao o motivo."""
    for command in commands:
        try:
            result = subprocess.run(
                shlex.split(command, posix=os.name != "nt"),
                cwd=root, text=True, encoding="utf-8", errors="replace", capture_output=True,
            )
        except FileNotFoundError:
            return f"portao: comando nao encontrado: {command}"
        if result.returncode != 0:
            tail = "\n".join((result.stdout + result.stderr).strip().splitlines()[-TAIL_LINES:])
            return f"portao falhou em `{command}` (exit {result.returncode}):\n{tail}"
    return None


__all__ = ["GATE_FILE", "clean_tree", "describe_pass", "gate_commands", "passed_entry", "record_pass", "run_gate"]
