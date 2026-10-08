"""CLI handler: changelog add|compile (D-121)."""

from __future__ import annotations

import argparse

from _changelog import add_fragment, changelog_settings, compile_fragments, work_root
from _clock import today
from _constants import PROCESS_FILE
from _state import read_json
from _tasks import find_task_or_current


def cmd_changelog(args: argparse.Namespace) -> int:
    settings = changelog_settings(read_json(PROCESS_FILE, {}))
    root = work_root()
    if args.action == "add":
        task = find_task_or_current(args.task_id)
        path = add_fragment(root, settings, task, args.category, args.text)
        print(f"+ {path.relative_to(root).as_posix()}")
        return 0
    date = args.date or (today() if args.version else None)
    consumed = compile_fragments(root, settings, args.version, date)
    if not consumed and not args.version:
        print("Nenhum fragmento: CHANGELOG inalterado.")
        return 0
    print(f"{settings['file']}: {len(consumed)} fragmento(s) compilado(s)" + (f" na versao {args.version}" if args.version else " no [Unreleased]"))
    for path in consumed:
        print(f"  - {path.relative_to(root).as_posix()}")
    return 0


__all__ = ["cmd_changelog"]
