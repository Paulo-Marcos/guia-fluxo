"""CLI handler: worktree add|remove (D-113)."""

from __future__ import annotations

import argparse

from _tasks import find_task_or_current, save_task
from _worktree import create_worktree, remove_worktree


def cmd_worktree(args: argparse.Namespace) -> int:
    """Cria ou remove o worktree de uma demanda que ja existe.

    `add` segue os modelos de `delivery.worktree` (caminho, branch, ponto de
    partida, envFiles, juncoes); `remove` desfaz as juncoes e recusa se sobrar
    link. Sem id, vale a branch (D-110) e depois o ponteiro.
    """
    task = find_task_or_current(args.task_id)
    if args.action == "add":
        worktree = create_worktree(task, args.path, args.branch)
        save_task(task)
        print(f"WORKTREE_PATH={worktree['path']}")
        print(f"WORKTREE_BRANCH={worktree['branch']}")
        if worktree["junctions"]:
            print(f"WORKTREE_JUNCTIONS={','.join(worktree['junctions'])}")
        return 0
    remove_worktree(task, force=args.force)
    save_task(task)
    print(f"{task['id']}: worktree removido ({task['worktree']['path']}).")
    return 0


__all__ = ["cmd_worktree"]
