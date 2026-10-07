"""CLI handlers: docs-check / render / commit-message."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

from _commit import compose_commit_message
from _constants import DOCS_MAP_FILE, ROOT
from _docs_hook import (
    compute_docs_candidates,
    load_docs_map,
    print_docs_block,
)
from _git_ops import git_changed_files
from _paths import relative
from _tasks import find_task_or_current


def cmd_docs_check(args: argparse.Namespace) -> int:
    task = find_task_or_current(args.task_id)
    docs_map = load_docs_map()
    if docs_map is None:
        payload = {"hasMap": False, "candidates": []}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(
                f"docs-check: {relative(DOCS_MAP_FILE)} nao existe. "
                "Projeto sem controle de docs. (docs/reference/docs-map.md)"
            )
        return 0
    changed_files = git_changed_files()
    candidates = compute_docs_candidates(task, changed_files, docs_map)
    if args.json:
        print(
            json.dumps(
                {"hasMap": True, "taskId": task.get("id"), "candidates": candidates},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if not candidates:
        print(f"docs-check: {task.get('id')} - nenhum candidato. Nada a fazer.")
        return 0
    print_docs_block(task, candidates)
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    render_script = ROOT / "core" / "build" / "render-skills.py"
    if not render_script.exists():
        print(f"missing: {relative(render_script)}", file=sys.stderr)
        return 2
    cmd = [sys.executable, str(render_script)]
    if args.check:
        cmd.append("--check")
    if args.verb:
        cmd.extend(["--verb", args.verb])
    return subprocess.call(cmd)


def cmd_commit_message(args: argparse.Namespace) -> int:
    """Imprime a mensagem de commit da demanda no formato configurado (D-112).

    No modo `pr` o `finish` nao commita (D-111): quem commita e monta o
    squash e o agente, e esta e a mensagem que ele usa (`git commit -F`,
    `gh pr merge --body-file`). Sem id, vale a branch (D-110) e depois o
    ponteiro, como nos demais verbos.
    """
    task = find_task_or_current(args.task_id)
    subject = args.subject or task.get("commitSubject")
    message = compose_commit_message(task, args.unlock_reason, args.body, subject)
    sys.stdout.write(message.rstrip("\n") + "\n")
    return 0


__all__ = ["cmd_commit_message", "cmd_docs_check", "cmd_render"]
