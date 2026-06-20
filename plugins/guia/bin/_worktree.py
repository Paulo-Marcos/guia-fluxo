"""Worktree creation/cleanup for promoted tasks.

Branch: codex/<slug>
Path:   .claude/worktrees/<slug>

Fixes:
- attach_worktree pre-checks branch existence (achado 2.13)
- cleanup is a no-op when --no-commit is used (achado 2.9)
"""

from __future__ import annotations

import argparse
from typing import Any

from _clock import today
from _constants import ROOT
from _git_ops import git_branch_exists, git_worktree_add, git_worktree_remove
from _paths import slugify


def attach_worktree(
    task: dict[str, Any],
    args: argparse.Namespace,
    item: dict[str, Any],
) -> None:
    slug = slugify(f"{task['id']}-{item['title']}")
    path = args.worktree_path or f".claude/worktrees/{slug}"
    branch = args.branch or f"codex/{slug}"
    task["worktree"] = {
        "enabled": True,
        "path": path,
        "branch": branch,
        "created": False,
        "removeOnFinish": args.remove_worktree_on_finish,
    }
    if not args.create_worktree:
        return
    if git_branch_exists(branch):
        raise SystemExit(
            f"Branch ja existe: {branch}. Use --branch <outro-nome> ou apague o anterior."
        )
    absolute_path = ROOT / path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    git_worktree_add(branch, absolute_path)
    task["worktree"]["created"] = True


def cleanup_task_worktree(task: dict[str, Any], commit_requested: bool) -> None:
    worktree = task.get("worktree") or {}
    if not worktree.get("enabled") or not worktree.get("removeOnFinish"):
        return
    # --no-commit means "dry close": leave the worktree alone (achado 2.9)
    if not commit_requested:
        return
    path = worktree.get("path")
    if not path:
        return
    absolute_path = (ROOT / path).resolve()
    if absolute_path == ROOT.resolve():
        print("WORKTREE_CLEANUP_SKIPPED=current-root")
        return
    if not absolute_path.exists():
        worktree["removedAt"] = today()
        worktree["created"] = False
        return
    git_worktree_remove(absolute_path, force=True)
    worktree["removedAt"] = today()
    worktree["created"] = False


__all__ = ["attach_worktree", "cleanup_task_worktree"]
