"""Thin wrappers around git CLI.

Centralizes:
- safe.directory injection
- friendly diagnostics when git is missing (achado 2.12)
- staged/changed file listing
- commit
- worktree create/remove

Returns Python data, raises SystemExit only when truly fatal. Keep this
module the only place that calls `subprocess.run([git, ...])`.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

from _constants import MSG_GIT_NOT_FOUND, ROOT


def has_git() -> bool:
    return shutil.which("git") is not None


def _ensure_git() -> None:
    if not has_git():
        raise SystemExit(MSG_GIT_NOT_FOUND)


def git_command(*args: str) -> list[str]:
    return ["git", "-c", f"safe.directory={ROOT.as_posix()}", *args]


def run_git(*args: str, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    _ensure_git()
    return subprocess.run(
        git_command(*args),
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=capture,
    )


def current_branch() -> str | None:
    """Branch da arvore onde o comando roda (CWD), ou None (destacado, sem git).

    D-110: no modo `pr` a raiz do estado (ROOT) e a arvore principal; a branch
    que identifica a demanda e a do worktree de onde o comando foi chamado.
    """
    try:
        output = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=Path.cwd(),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None
    return output if output and output != "HEAD" else None


def git_changed_files() -> list[str]:
    if not has_git():
        return []
    try:
        output = subprocess.check_output(
            git_command("diff", "--name-only", "--diff-filter=ACMR", "HEAD"),
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def name_status_against_base(files: Iterable[str], base_branch: str) -> list[str]:
    """Linhas `name-status` dos `files` contra a base da branch atual (D-112).

    Base = merge-base de HEAD com `origin/<base_branch>` (o que o PR vai
    mostrar); sem remoto, HEAD. Compara a arvore de trabalho com a base, entao
    conta o que ja foi commitado na branch e o que ainda nao foi. Arquivo
    novo nao rastreado (e nao ignorado) entra como `A`. Roda no CWD: no modo
    `pr` e o worktree da demanda, nao a principal.
    """
    files_list = list(files)
    if not files_list:
        return []
    cwd = Path.cwd()

    def _out(*args: str) -> str | None:
        result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True)
        return result.stdout if result.returncode == 0 else None

    base = (_out("merge-base", "HEAD", f"origin/{base_branch}") or "").strip() or "HEAD"
    tracked = _out("diff", "--name-status", "--no-renames", base, "--", *files_list) or ""
    untracked = _out("ls-files", "--others", "--exclude-standard", "--", *files_list) or ""
    lines = [line for line in tracked.splitlines() if line.strip()]
    lines += [f"A\t{path}" for path in untracked.splitlines() if path.strip()]
    return lines


def git_ignored_files(files: Iterable[str]) -> set[str]:
    """Subconjunto de `files` que o .gitignore ignora (D-111, D-579).

    `git check-ignore` sai 1 quando nenhum e ignorado e 0 listando os que
    sao; arquivo versionado nunca conta como ignorado (sem `--no-index`).
    """
    files_list = list(files)
    if not files_list:
        return set()
    result = subprocess.run(
        git_command("check-ignore", "--", *files_list),
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode not in (0, 1):
        return set()
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def git_staged_files() -> list[str]:
    if not has_git():
        return []
    try:
        output = subprocess.check_output(
            git_command("diff", "--cached", "--name-only", "--diff-filter=ACMR"),
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def git_commit(files: Iterable[str], message: str) -> None:
    _ensure_git()
    files_list = list(files)
    # D-081: `git add -- <path>` falha com "pathspec did not match any files"
    # quando o arquivo da task foi deletado, abortando o commit. `git add -A`
    # (restrito aos pathspecs da task) reconcilia o index com o working tree,
    # cobrindo adicoes, modificacoes E delecoes no mesmo stage.
    subprocess.run(git_command("add", "-A", "--", *files_list), cwd=ROOT, check=True)
    # D-105: commit ESCOPADO ao pathspec da demanda. Sem `-- <files>`, o
    # `git commit` sela o INDEX inteiro - engolindo o que outra demanda (outro
    # chat/agente rodando em paralelo na mesma arvore) tenha dado `git add`.
    # Com o pathspec, so os caminhos desta demanda entram no commit, mesmo com
    # o index sujo de trabalho concorrente. E o que torna o `--no-commit` +
    # staging manual desnecessario como isolamento.
    subprocess.run(
        git_command("commit", "-m", message, "--", *files_list), cwd=ROOT, check=True
    )


def git_branch_exists(branch: str) -> bool:
    if not has_git():
        return False
    try:
        result = subprocess.run(
            git_command("rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"),
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def git_worktree_add(branch: str, path: Path) -> None:
    _ensure_git()
    subprocess.run(
        git_command("worktree", "add", "-b", branch, str(path)),
        cwd=ROOT,
        check=True,
    )


def git_worktree_remove(path: Path, force: bool = False) -> None:
    _ensure_git()
    command = git_command("worktree", "remove", str(path))
    if force:
        command.append("--force")
    subprocess.run(command, cwd=ROOT, check=True)


def git_log_grep(pattern: str) -> str:
    if not has_git():
        return ""
    if not (ROOT / ".git").exists():
        return ""
    try:
        return subprocess.check_output(
            git_command(
                "log",
                "--fixed-strings",
                "--grep",
                pattern,
                "--pretty=format:%h|%ad|%s",
                "--date=short",
            ),
            text=True,
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def git_staged_name_status() -> list[str]:
    if not has_git():
        return []
    try:
        return subprocess.check_output(
            ["git", "diff", "--cached", "--name-status", "--diff-filter=ACMRD"],
            text=True,
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
        ).splitlines()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


__all__ = [
    "has_git",
    "git_command",
    "run_git",
    "current_branch",
    "git_changed_files",
    "git_ignored_files",
    "name_status_against_base",
    "git_staged_files",
    "git_commit",
    "git_branch_exists",
    "git_worktree_add",
    "git_worktree_remove",
    "git_log_grep",
    "git_staged_name_status",
]
