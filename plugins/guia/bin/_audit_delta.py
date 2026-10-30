"""Auditoria de delta (D-140, D-207): o head mudou desde a ultima auditoria.

D-140 abriu o delta depois de uma auditoria aprovada; a D-207 estende a
auditoria reprovada: a correcao dos achados nao pede o diff inteiro de novo,
pede o que mudou desde o head auditado - cada achado anterior conferido como
fechado e o que a correcao tocou no que ja estava ok.

O delta volta a ser completo quando nao se le com seguranca: falta um dos
quatro SHAs, o delta e grande, toca caminho sensivel (workflows, hooks,
travas, configuracao do agente, dependencias, seguranca) ou traz `[unlock:]`
novo. O motor decide pelo git, nunca pelo que o agente declara.
"""

from __future__ import annotations

import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

from _autonomy import _matches
from _commit import unlock_marks
from _git_ops import git_output

MODE_DELTA = "delta"
MODE_FULL = "full"
DELTA_MAX_LINES_DEFAULT = 300
# Abaixo disso o delta e pequeno demais para a regra da metade valer a pena.
DELTA_RATIO_FLOOR = 50
DELTA_FULL_PATHS = (
    ".github/**",
    ".githooks/**",
    ".guia/locks/**",
    ".claude/settings*.json",
    "AGENTS.md",
    "CLAUDE.md",
    "**/requirements*.txt",
    "**/package.json",
    "**/package-lock.json",
    "**/pyproject.toml",
    "*auth*",
    "*secret*",
    "*credential*",
    "*token*",
    "*security*",
)
_FILE_HEADER = re.compile(r"^diff --git a/(.+?) b/(.+)$")
_MODE_LINES = ("old mode ", "new mode ", "new file mode ", "deleted file mode ")


def _file_patches(root: Path, base: str, head: str) -> dict[str, Counter[str]] | None:
    """Linhas `+`/`-` do PR por arquivo, sem cabecalho de hunk: rebase limpo nao muda nada.

    Sem renames (mover `.github/workflows/ci.yml` vira remocao + adicao, com
    linhas), e o que nao tem linha tambem conta: modo do arquivo e binario
    (pelo blob do head). Caminho que o git poe entre aspas nao se le com
    seguranca: None, e a auditoria e completa.
    """
    result = subprocess.run(["git", "-c", "core.quotePath=false", "diff", "--no-color", "--no-ext-diff",
                             "--no-renames", "--full-index", "--unified=0", f"{base}..{head}"],
                            cwd=root, capture_output=True)
    if result.returncode != 0:
        return None
    patches: dict[str, Counter[str]] = {}
    current: Counter[str] = Counter()
    in_hunk, post_blob = False, ""
    for line in result.stdout.decode("utf-8", errors="replace").splitlines():
        if line.startswith("diff --git "):
            header = _FILE_HEADER.match(line)
            if not header:
                return None
            current, in_hunk, post_blob = patches.setdefault(header.group(2), Counter()), False, ""
        elif line.startswith("@@"):
            in_hunk = True
        elif in_hunk:
            if line[:1] in "+-":
                current[line] += 1
        elif line.startswith("index "):
            post_blob = line.split()[1].split("..")[-1]
        elif line.startswith(_MODE_LINES):
            current[line] += 1
        elif line.startswith("Binary files "):
            current[f"binary {post_blob}"] += 1
    return patches


def _unlocks(root: Path, base: str, head: str) -> set[str]:
    return unlock_marks(git_output(root, "log", "--format=%B", f"{base}..{head}") or "")


def _measure(root: Path, old: tuple[str, str], new: tuple[str, str]) -> dict[str, Any] | None:
    before, after = _file_patches(root, *old), _file_patches(root, *new)
    if before is None or after is None:
        return None
    files, lines = [], 0
    for path in sorted(set(before) | set(after)):
        old_lines, new_lines = before.get(path, Counter()), after.get(path, Counter())
        changed = sum(((old_lines - new_lines) + (new_lines - old_lines)).values())
        if changed:
            files.append(path)
            lines += changed
    total = sum(sum(c.values()) for c in after.values())
    return {"files": files, "lines": lines, "total": total,
            "newUnlocks": sorted(_unlocks(root, *new) - _unlocks(root, *old))}


def _full_reason(measure: dict[str, Any], config: dict[str, Any]) -> str | None:
    audit_cfg = (config.get("delivery") or {}).get("audit") or {}
    try:
        max_lines = int(audit_cfg.get("deltaMaxLines") or DELTA_MAX_LINES_DEFAULT)
    except (TypeError, ValueError):
        max_lines = DELTA_MAX_LINES_DEFAULT
    lines = measure["lines"]
    if lines > max_lines:
        return f"delta grande ({lines} linhas > {max_lines})"
    if lines > DELTA_RATIO_FLOOR and lines * 2 > measure["total"]:
        return f"delta e mais da metade do PR ({lines} de {measure['total']} linhas)"
    patterns = DELTA_FULL_PATHS + tuple((config.get("autonomy") or {}).get("alwaysHuman") or ())
    sensitive = sorted({p for p in measure["files"] for pat in patterns if _matches(p.lower(), pat)})
    if sensitive:
        return "delta toca caminho sensivel: " + ", ".join(sensitive)
    if measure["newUnlocks"]:
        return "delta traz [unlock:] novo: " + ", ".join(measure["newUnlocks"])
    return None


def delta_plan(root: Path, previous: dict[str, Any] | None, target: dict[str, Any],
               config: dict[str, Any]) -> dict[str, Any] | None:
    """Head novo desde a ultima auditoria (aprovada ou reprovada): delta ou completa, e por que.

    None quando nao ha auditoria anterior ou o head e o mesmo. Senao, o plano
    com `mode` (`delta`/`full`), `from` (head auditado), `fromResult`, `range`
    (`<base-velha>..<head-velho> <base-nova>..<head-novo>` do range-diff) e,
    quando completa, `reason`.
    """
    if not previous or not previous.get("auditedSha"):
        return None
    old_head, old_base, head, base = previous["auditedSha"], previous.get("auditedBase"), target["head"], target.get("base")
    if old_head == head:
        return None
    plan: dict[str, Any] = {"from": old_head, "fromResult": previous.get("result"), "mode": MODE_FULL}
    if not (old_base and head and base):
        return {**plan, "reason": "falta a base ou o head de uma das auditorias"}
    if any(git_output(root, "cat-file", "-e", f"{sha}^{{commit}}") is None for sha in (old_head, old_base)):
        return {**plan, "reason": "o head auditado nao esta no repositorio local"}
    plan["range"] = f"{old_base}..{old_head} {base}..{head}"
    measure = _measure(root, (old_base, old_head), (base, head))
    if measure is None:
        return {**plan, "reason": "o git nao mediu o delta"}
    plan.update(files=measure["files"], lines=measure["lines"])
    reason = _full_reason(measure, config)
    return {**plan, "reason": reason} if reason else {**plan, "mode": MODE_DELTA}


__all__ = ["DELTA_FULL_PATHS", "DELTA_MAX_LINES_DEFAULT", "MODE_DELTA", "MODE_FULL", "delta_plan"]
