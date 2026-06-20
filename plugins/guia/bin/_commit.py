"""Build the commit for a finished task.

Centralizes the normalization step (Windows backslash -> forward slash)
that previously caused `commit_task` to see staged files as unrelated
(achado 2.4).
"""

from __future__ import annotations

import subprocess
from typing import Any

from _constants import (
    MSG_GIT_NOT_FOUND,
    MSG_NO_FILES_FOR_COMMIT,
    MSG_NONE_PLACEHOLDER,
    MSG_UNRELATED_STAGED,
)
from _git_ops import git_commit, git_staged_files, has_git
from _paths import normalize_path


def commit_task(task: dict[str, Any]) -> None:
    files = [value for value in task.get("modifiedFiles", []) if value != MSG_NONE_PLACEHOLDER]
    if not files:
        raise SystemExit(MSG_NO_FILES_FOR_COMMIT)
    if not has_git():
        raise SystemExit(MSG_GIT_NOT_FOUND)
    expected = {normalize_path(value) for value in files}
    staged = {normalize_path(value) for value in git_staged_files()}
    unexpected = sorted(staged - expected)
    if unexpected:
        names = ", ".join(unexpected)
        raise SystemExit(MSG_UNRELATED_STAGED.format(names=names))
    message = f"{task['kind']}: {task['title']}\n\nTask: {task['id']}"
    try:
        git_commit(files, message)
    except FileNotFoundError:
        raise SystemExit(MSG_GIT_NOT_FOUND)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode)


__all__ = ["commit_task"]
