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
    subprocess.run(git_command("add", "--", *files_list), cwd=ROOT, check=True)
    subprocess.run(git_command("commit", "-m", message), cwd=ROOT, check=True)


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
    "git_changed_files",
    "git_staged_files",
    "git_commit",
    "git_branch_exists",
    "git_worktree_add",
    "git_worktree_remove",
    "git_log_grep",
    "git_staged_name_status",
]
