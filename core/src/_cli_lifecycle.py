"""CLI handlers: init / status / ready / finish / validate.

Each handler is a thin orchestration over the domain/infrastructure
modules: they parse argparse Namespace and call into _tasks, _docs_hook,
_commit, _locks, etc.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from _commit import commit_task
from _constants import (
    AI_DIR,
    CHAT_TITLE_FILE,
    DOCS_MAP_FILE,
    MSG_DEFAULT_FINISH_SUMMARY,
    MSG_DEFAULT_READY_SUMMARY,
    MSG_DEFAULT_VALIDATE_SUMMARY,
    MSG_DEFAULT_VALIDATION_PENDING,
    MSG_PROCESS_FILES_OK,
    MSG_VALIDATE_DEPRECATED,
    BACKLOG_FILE,
    CURRENT_FILE,
    PROCESS_FILE,
    ROOT,
    STATUS_AWAITING_VALIDATION,
    STATUS_VALIDATED,
    TASKS_FILE,
)
from _docs_hook import (
    build_docs_review_record,
    ensure_docs_review_ok,
    load_docs_map,
)
from _features_md import upsert_features_entry
from _git_ops import git_changed_files
from _locks import lock_task_files
from _paths import relative
from _process_config import default_process
from _reports import write_report
from _state import read_json, write_if_missing, write_json
from _tasks import (
    find_task_or_current,
    merge_list,
    print_chat_title,
    save_task,
    set_current_task,
)
from _validation_runner import run_validation_commands
from _worktree import cleanup_task_worktree


def cmd_init(args: argparse.Namespace) -> int:
    AI_DIR.mkdir(exist_ok=True)
    write_if_missing(
        PROCESS_FILE,
        default_process(args.project_name),
        force=args.force,
    )
    write_if_missing(TASKS_FILE, {"schemaVersion": 1, "tasks": []}, force=args.force)
    write_if_missing(BACKLOG_FILE, {"schemaVersion": 1, "items": []}, force=args.force)
    write_if_missing(CURRENT_FILE, {}, force=args.force)
    if args.force or not CHAT_TITLE_FILE.exists():
        CHAT_TITLE_FILE.write_text("", encoding="utf-8")
    print(f"AI process initialized for {args.project_name}.")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    import json

    task = find_task_or_current(args.task_id)
    print(json.dumps(task, ensure_ascii=False, indent=2))
    print_chat_title(task)
    return 0


def cmd_ready(args: argparse.Namespace) -> int:
    task = find_task_or_current(args.task_id)
    config = read_json(PROCESS_FILE, default_process(ROOT.name))
    changed_files = args.file or git_changed_files()
    task["status"] = config.get("ready", {}).get("status", STATUS_AWAITING_VALIDATION)
    merge_list(task, "modifiedFiles", changed_files)
    merge_list(task, "summary", args.summary or [MSG_DEFAULT_READY_SUMMARY])
    merge_list(task, "validations", args.validation)
    task["pending"] = args.pending or [MSG_DEFAULT_VALIDATION_PENDING]

    if args.run_tests or config.get("ready", {}).get("runValidationByDefault", False):
        run_validation_commands(task, config, "ready")

    save_task(task)
    set_current_task(task)
    upsert_features_entry(task)
    write_report(task, "ready")

    print(f"{task['id']} moved to {task['status']}.")
    print_chat_title(task)
    return 0


def cmd_finish(args: argparse.Namespace) -> int:
    task = find_task_or_current(args.task_id)
    config = read_json(PROCESS_FILE, default_process(ROOT.name))
    changed_files = args.file or git_changed_files()

    docs_map = load_docs_map()
    if docs_map is not None:
        ensure_docs_review_ok(task, changed_files, docs_map, args)
    else:
        print(
            "docs-check: .ai/docs-map.yaml nao encontrado. "
            "Pulando hook de docs. "
            "Crie o mapa para ativar o controle de docs (docs/reference/docs-map.md).",
            file=sys.stderr,
        )

    finish_config = config.get("finish", {})
    task["status"] = finish_config.get("status", STATUS_VALIDATED)
    merge_list(task, "modifiedFiles", changed_files)
    merge_list(task, "modifiedFiles", args.docs_touched)
    merge_list(task, "summary", args.summary or [MSG_DEFAULT_FINISH_SUMMARY])
    merge_list(task, "validations", args.validation)
    task["pending"] = args.pending or []
    if docs_map is not None:
        task["docsReview"] = build_docs_review_record(
            task, changed_files, docs_map, args
        )

    if args.run_tests or finish_config.get("runValidationByDefault", False):
        run_validation_commands(task, config, "finish")

    if args.lock or finish_config.get("lockOnFinish", False):
        lock_task_files(task, args.lock_id, args.lock_description)
        merge_list(task, "modifiedFiles", ["features/registry.yaml"])
        merge_list(task, "summary", [f"Lock `{args.lock_id}` registrado para os arquivos finalizados."])

    commit_requested = args.commit
    if commit_requested is None:
        commit_requested = finish_config.get("commitByDefault", True)

    save_task(task)
    set_current_task(task)
    upsert_features_entry(task)
    write_report(task, "finish")

    if commit_requested:
        commit_task(task)
    cleanup_task_worktree(task, commit_requested)

    print(f"{task['id']} finished as {task['status']}.")
    print_chat_title(task)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    print(MSG_VALIDATE_DEPRECATED, file=sys.stderr)
    task = find_task_or_current(args.task_id)
    config = read_json(PROCESS_FILE, default_process(ROOT.name))
    task["status"] = config.get("validate", {}).get("status", STATUS_VALIDATED)
    merge_list(task, "modifiedFiles", args.file)
    merge_list(task, "summary", args.summary or [MSG_DEFAULT_VALIDATE_SUMMARY])
    task["pending"] = []

    save_task(task)
    set_current_task(task)
    upsert_features_entry(task)
    write_report(task, "validate")

    if args.lock:
        lock_task_files(task, args.lock_id, args.lock_description)

    print(f"{task['id']} marked as {task['status']}.")
    print_chat_title(task)
    return 0


def cmd_doctor(_args: argparse.Namespace) -> int:
    required = [PROCESS_FILE, TASKS_FILE, BACKLOG_FILE, CURRENT_FILE]
    missing = [path for path in required if not path.exists()]
    if missing:
        for path in missing:
            print(f"missing: {relative(path)}")
        return 1
    print(MSG_PROCESS_FILES_OK)
    return 0


__all__ = [
    "cmd_init",
    "cmd_status",
    "cmd_ready",
    "cmd_finish",
    "cmd_validate",
    "cmd_doctor",
]
