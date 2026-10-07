"""doctor: o hook commit-msg vai rodar? (D-115, R10)

O `commit-msg` e a primeira linha de defesa das travas, e pode ficar mudo sem
ninguem ver. Em 01/10 a `pr-audit` gravou `core.hooksPath = NUL` na config
COMUM do clone, e o app do Claude copiou para cada worktree novo (kaizen da
D-851 no gerador-cortes). Aqui o valor e conferido onde o comando roda (o
worktree), na config comum e no `config.worktree`. So avisos: o doctor nao
reprova por isso (`--strict` promove).
"""

from __future__ import annotations

from pathlib import Path

from _constants import REGISTRY_FILE
from _git_ops import git_output

HOOKS_PATH_KEY = "core.hooksPath"
_NULL_VALUES = {"", "nul", "nul:", "/dev/null"}


def _is_null(value: str) -> bool:
    return value.strip().lower() in _NULL_VALUES


def _hooks_dir(cwd: Path, effective: str | None) -> Path | None:
    """Pasta onde o git procura os hooks para este worktree."""
    if effective is None:
        default = git_output(cwd, "rev-parse", "--git-path", "hooks")
        return (cwd / default).resolve() if default else None
    candidate = Path(effective)
    if candidate.is_absolute():
        return candidate
    toplevel = git_output(cwd, "rev-parse", "--show-toplevel")
    return (Path(toplevel) / candidate) if toplevel else None


def hooks_path_warnings(cwd: Path | None = None) -> list[str]:
    cwd = cwd or Path.cwd()
    if git_output(cwd, "rev-parse", "--is-inside-work-tree") != "true":
        return []
    warnings: list[str] = []
    effective = git_output(cwd, "config", "--get", HOOKS_PATH_KEY)
    common = git_output(cwd, "config", "--local", "--get", HOOKS_PATH_KEY)
    per_worktree = None
    if git_output(cwd, "config", "--bool", "--get", "extensions.worktreeConfig") == "true":
        per_worktree = git_output(cwd, "config", "--worktree", "--get", HOOKS_PATH_KEY)
    if per_worktree is not None and per_worktree != common:
        warnings.append(
            f"{HOOKS_PATH_KEY} no config.worktree ({per_worktree}) difere da config comum "
            f"({common if common is not None else 'nao definido'}); vale o do worktree. "
            "Remova com `git config --worktree --unset core.hooksPath`."
        )
    if effective is not None and _is_null(effective):
        warnings.append(
            f"{HOOKS_PATH_KEY} = {effective!r}: hooks desligados - o commit-msg das travas "
            "nao roda. Aponte para a pasta dos hooks (`git config core.hooksPath .githooks`) "
            "ou rode `guia init`."
        )
        return warnings
    hooks_dir = _hooks_dir(cwd, effective)
    if hooks_dir is not None and (hooks_dir / "commit-msg").is_file():
        return warnings
    if effective is None:
        if REGISTRY_FILE.exists():
            warnings.append(
                f"{HOOKS_PATH_KEY} nao configurado e sem commit-msg em .git/hooks: as travas "
                "so sao conferidas no CI. Rode `guia init` (configura .githooks)."
            )
        return warnings
    warnings.append(f"{HOOKS_PATH_KEY} = {effective!r}: sem commit-msg em {hooks_dir}.")
    return warnings


__all__ = ["hooks_path_warnings"]
