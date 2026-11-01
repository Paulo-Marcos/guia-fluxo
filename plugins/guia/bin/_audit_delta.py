"""Auditoria de delta (D-140, D-207): o head mudou desde a ultima auditoria.

D-140 abriu o delta depois de uma auditoria aprovada; a D-207 estende a
auditoria reprovada: a correcao dos achados nao pede o diff inteiro de novo,
pede o que mudou desde o head auditado - cada achado anterior conferido como
fechado e o que a correcao tocou no que ja estava ok.

O delta volta a ser completo quando nao se le com seguranca: falta um dos
quatro SHAs, o delta e grande, toca caminho sensivel (workflows, hooks,
travas, configuracao do agente, dependencias, seguranca) ou traz `[unlock:]`
novo. O motor decide pelo git, nunca pelo que o agente declara.

D-211: a copia gerada identica a fonte (`delivery.audit.mirrors`) conta uma
vez so na regua; binario que muda no delta pede a auditoria completa.
"""

from __future__ import annotations

import subprocess
from difflib import SequenceMatcher
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
# Caminhos do proprio projeto entram por `autonomy.alwaysHuman`.
DELTA_FULL_PATHS = (
    ".github/**",
    ".githooks/**",
    "**/hooks/**",
    ".guia/locks/**",
    "core/lock/**",
    ".claude/**",
    "**/.gitattributes",
    "**/agents.md",
    "**/claude.md",
    ".claude-plugin/**",
    "**/.claude-plugin/**",
    ".guia/process.json",
    # As travas e a propria regua do delta (e o que a alimenta): afrouxar qualquer um esconde o resto.
    "**/check-lock.py",
    "**/_locks.py",
    "**/lock_api.py",
    "**/_audit_delta.py",
    "**/_audit.py",
    "**/_cli_audit.py",
    "**/_autonomy.py",
    "**/_commit.py",
    "**/_git_ops.py",
    "**/_state.py",
    "**/_constants.py",
    "**/_tasks.py",
    "**/_changelog.py",
    "**/_github.py",
    "**/_auto_finish.py",
    "**/_skills.py",
    "**/_conductor.py",
    # Pontos de entrada, o texto que orienta o auditor e as travas que vao para outros projetos.
    "**/guia.py",
    "**/guia.ps1",
    "core/manifest/**",
    "**/audit-checklist.md",
    "**/commands/audit.md",
    "**/.agents/skills/**",
    "**/templates/locks/**",
    "**/templates/scaffold/auditoria.yml",
    "core/build/**",
    "**/conftest.py",
    "**/pytest.ini",
    "**/vitest.config.*",
    "**/jest.config.*",
    "**/vite.config.*",
    "**/eslint.config.*",
    "**/.eslintrc*",
    "**/pyrightconfig.json",
    "**/.gitmodules",
    "**/tox.ini",
    "**/.pre-commit-config.yaml",
    "**/setup.py",
    "**/setup.cfg",
    "**/pyproject.toml",
    "**/requirements*.txt",
    "**/pipfile*",
    "**/*.lock",
    "**/*.lockb",
    "**/package.json",
    "**/package-lock.json",
    "**/npm-shrinkwrap.json",
    "**/pnpm-lock.yaml",
    "**/.npmrc",
    "*auth*",
    "*secret*",
    "*credential*",
    "*token*",
    "*security*",
)
_MODE_LINES = ("old mode ", "new mode ", "new file mode ", "deleted file mode ")
# Cabecalho de arquivo que a medida entende; qualquer outra linha antes do hunk = nao medido.
_KNOWN_HEADER = ("diff --git ", "index ", "--- ", "+++ ", *_MODE_LINES)
# A config do usuario nao esconde nada: submodulo aparece, textconv/diff externo ficam de fora.
# `--text`: um `.gitattributes` com `-diff` nao transforma texto em "Binary files differ".
_DIFF = ["diff", "--no-color", "--no-ext-diff", "--no-textconv", "--text", "--no-renames",
         "--ignore-submodules=none", "--submodule=short"]
# Binario de verdade sai sem `--text`: lido linha a linha seria lento, e mudar binario ja e completa.
_DIFF_BINARY = [arg for arg in _DIFF if arg != "--text"]


class Unmeasurable(Exception):
    """A medida nao entendeu algo do diff: a auditoria e completa (falha fechada)."""


def _git_bytes(root: Path, *args: str) -> bytes:
    result = subprocess.run(["git", "-c", "core.quotePath=false", *args], cwd=root, capture_output=True)
    if result.returncode != 0:
        raise Unmeasurable(f"git {args[0]} falhou")
    return result.stdout


def _binaries(root: Path, base: str, head: str) -> set[str]:
    """O que o git trata como binario (`-\\t-` no numstat, sem `--text`): leva o marcador do blob."""
    out = _git_bytes(root, *_DIFF_BINARY, "--numstat", "-z", f"{base}..{head}")
    entries = out.decode("utf-8", errors="surrogateescape").split("\0")
    return {entry.split("\t", 2)[2] for entry in entries if entry.startswith("-\t-\t")}


def _file_lines(root: Path, base: str, head: str, path: str, binary: bool = False) -> list[str]:
    """O patch de um arquivo, na ordem, sem cabecalho de hunk: rebase limpo nao muda nada.

    Conta tambem o que nao e linha de conteudo: modo, binario (pelo blob do
    head, sem `--text`) e `\\ No newline at end of file`. Bytes nao UTF-8
    viram `surrogateescape` (sem perda). Linha de cabecalho desconhecida ou arquivo listado sem nada
    medido levantam `Unmeasurable`.
    """
    out = _git_bytes(root, *(_DIFF_BINARY if binary else _DIFF), "--full-index", "--unified=0", f"{base}..{head}",
                     "--", f":(literal){path}")
    lines: list[str] = []
    in_hunk, post_blob = False, ""
    for line in out.decode("utf-8", errors="surrogateescape").splitlines():
        if line.startswith("@@"):
            in_hunk = True
        elif in_hunk:
            lines.append(line)
        elif line.startswith("index "):
            post_blob = line.split()[1].split("..")[-1]
        elif line.startswith(_MODE_LINES):
            lines.append(line)
        elif line.startswith("Binary files "):
            lines.append(f"binary {post_blob}")
        elif not line.startswith(_KNOWN_HEADER):
            raise Unmeasurable(f"linha de diff nao reconhecida em {path}")
    if binary and f"binary {post_blob}" not in lines:
        lines.append(f"binary {post_blob}")
    if not lines:
        raise Unmeasurable(f"{path} esta no diff, mas o patch veio vazio")
    return lines


def _file_patches(root: Path, base: str, head: str) -> dict[str, list[str]]:
    return _side(root, base, head)[0]


def _side(root: Path, base: str, head: str) -> tuple[dict[str, list[str]], set[str]]:
    """Por arquivo do PR, as linhas do patch na ordem (a ordem muda o que o codigo faz), e os binarios.

    Os nomes vem de `--name-only -z`, nunca do cabecalho `diff --git a/X b/Y`
    (um caminho com ` b/` no meio cortaria errado). Sem renames: mover
    `.github/workflows/ci.yml` vira remocao + adicao, com linhas. Nome que nao
    e UTF-8 nao se le com seguranca: `Unmeasurable`.
    """
    names = _git_bytes(root, *_DIFF, "--name-only", "-z", f"{base}..{head}")
    try:
        decoded = names.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Unmeasurable("nome de arquivo fora de UTF-8") from exc
    binaries = _binaries(root, base, head)
    paths = filter(None, decoded.split("\0"))
    return {path: _file_lines(root, base, head, path, path in binaries) for path in paths}, binaries


def _changed(old: list[str], new: list[str]) -> int:
    """Linhas que saem ou entram de uma sequencia para a outra; trocar duas de lugar conta."""
    if old == new:
        return 0
    same = sum(block.size for block in SequenceMatcher(None, old, new, autojunk=False).get_matching_blocks())
    return len(old) + len(new) - 2 * same


def _unlocks(root: Path, base: str, head: str) -> set[str]:
    """Pelo `_git_bytes`: um `git log` que falha vira `Unmeasurable`, nunca "nenhuma marca"."""
    return unlock_marks(_git_bytes(root, "log", "--format=%B", f"{base}..{head}").decode("utf-8", errors="replace"))


def _mirrors(config: dict[str, Any]) -> dict[str, str]:
    """`delivery.audit.mirrors` (prefixo da copia -> prefixo da fonte); mapa malformado nao desconta nada."""
    mirrors = ((config.get("delivery") or {}).get("audit") or {}).get("mirrors")
    if not isinstance(mirrors, dict) or not all(isinstance(copy, str) and isinstance(source, str) and copy and source
                                                for copy, source in mirrors.items()):
        return {}
    return mirrors


def _echoes(before: dict[str, list[str]], after: dict[str, list[str]], mirrors: dict[str, str]) -> set[str]:
    """Copias do mapa cujo patch e o da fonte nos dois lados: o auditor le uma vez, a regua conta uma vez."""
    echoes = set()
    for path in set(before) | set(after):
        for copy, source in mirrors.items():
            src = source + path[len(copy):]
            if (path.startswith(copy) and src != path
                    and before.get(path) == before.get(src) and after.get(path) == after.get(src)):
                echoes.add(path)
    return echoes


def _measure(root: Path, old: tuple[str, str], new: tuple[str, str], config: dict[str, Any]) -> dict[str, Any]:
    """`lines` e `total` na mesma regua: linhas dos dois lados (antes + depois), sem os ecos do mapa."""
    (before, old_binaries), (after, new_binaries) = _side(root, *old), _side(root, *new)
    echoes = _echoes(before, after, _mirrors(config))
    files, lines = [], 0
    for path in sorted(set(before) | set(after)):
        changed = _changed(before.get(path, []), after.get(path, []))
        if changed:
            files.append(path)
            lines += 0 if path in echoes else changed
    total = sum(len(patch) for side in (before, after) for path, patch in side.items() if path not in echoes)
    return {"files": files, "lines": lines, "total": total,
            "binaries": [path for path in files if path in old_binaries | new_binaries],
            "newUnlocks": sorted(_unlocks(root, *new) - _unlocks(root, *old))}


def _sensitive(files: list[str], config: dict[str, Any]) -> list[str]:
    """Caixa baixa nos dois lados: `AGENTS.md` casa no Linux tambem."""
    patterns = [pat.lower() for pat in DELTA_FULL_PATHS + tuple((config.get("autonomy") or {}).get("alwaysHuman") or ())]
    return sorted({p for p in files for pat in patterns if _matches(p.lower(), pat)})


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
        return f"delta e mais da metade do PR ({lines} de {measure['total']} linhas, antes + depois)"
    sensitive = _sensitive(measure["files"], config)
    if sensitive:
        return "delta toca caminho sensivel: " + ", ".join(sensitive)
    if measure["binaries"]:
        return "delta toca binario: " + ", ".join(measure["binaries"])
    if measure["newUnlocks"]:
        return "delta traz [unlock:] novo: " + ", ".join(measure["newUnlocks"])
    return None


def verdict_label(result: str | None) -> str:
    return {"approved": "aprovada", "rejected": "reprovada"}.get(result or "", "anterior")


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
    # O range-diff (e o `git show`) respeita `-diff` do .gitattributes e esconde a linha; o auditor le com --text.
    # Sem textconv nem diff externo, como a medida: o astextplain do Git for Windows derruba o comando.
    plan["textDiff"] = f"git diff --text --no-textconv --no-ext-diff {old_head} {head}"
    try:
        measure = _measure(root, (old_base, old_head), (base, head), config)
    except Unmeasurable as exc:
        return {**plan, "reason": f"a medida do delta nao entendeu o diff ({exc})"}
    plan.update(files=measure["files"], lines=measure["lines"])
    reason = _full_reason(measure, config)
    return {**plan, "reason": reason} if reason else {**plan, "mode": MODE_DELTA}


__all__ = ["DELTA_FULL_PATHS", "DELTA_MAX_LINES_DEFAULT", "MODE_DELTA", "MODE_FULL", "delta_plan", "verdict_label"]
