"""CLI handlers: init / status / ready / finish / validate.

Each handler is a thin orchestration over the domain/infrastructure
modules: they parse argparse Namespace and call into _tasks, _docs_hook,
_commit, _locks, etc.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from _clock import today
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
    STATUS_BLOCKED,
    STATUS_CANCELLED,
    STATUS_FINISHED,
    STATUS_IN_DEVELOPMENT,
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


_TERMINAL_STATUSES = frozenset({STATUS_VALIDATED, STATUS_FINISHED, STATUS_CANCELLED})


def _clear_current_if_matches(task_id: str) -> None:
    current = read_json(CURRENT_FILE, {})
    if current.get("taskId") == task_id:
        write_json(CURRENT_FILE, {})
        CHAT_TITLE_FILE.write_text("", encoding="utf-8")


def cmd_cancel(args: argparse.Namespace) -> int:
    task = find_task_or_current(args.task_id)
    if task["status"] in _TERMINAL_STATUSES:
        raise SystemExit(
            f"Task {task['id']} ja esta em estado terminal ({task['status']}); nao pode ser cancelada."
        )

    task["status"] = STATUS_CANCELLED
    cancellation = {"reason": args.reason, "at": today()}
    task.setdefault("cancellations", []).append(cancellation)
    merge_list(task, "summary", [f"Cancelada em {today()}: {args.reason}"])
    task["pending"] = []

    save_task(task)
    upsert_features_entry(task)
    write_report(task, "cancel")

    if not args.keep_worktree:
        cleanup_task_worktree(task, commit_requested=True)
        save_task(task)

    if args.set_current:
        set_current_task(task)
    else:
        _clear_current_if_matches(task["id"])

    print(f"{task['id']} cancelled: {args.reason}")
    print_chat_title(task)
    return 0


def cmd_block(args: argparse.Namespace) -> int:
    task = find_task_or_current(args.task_id)
    if task["status"] in _TERMINAL_STATUSES:
        raise SystemExit(
            f"Task {task['id']} em estado terminal ({task['status']}); nao pode ser bloqueada."
        )
    if task["status"] == STATUS_BLOCKED:
        raise SystemExit(f"Task {task['id']} ja esta bloqueada.")

    task["status"] = STATUS_BLOCKED
    block_record = {"reason": args.reason, "at": today()}
    task.setdefault("blocks", []).append(block_record)
    merge_list(task, "summary", [f"Bloqueada em {today()}: {args.reason}"])

    save_task(task)
    set_current_task(task)
    upsert_features_entry(task)
    write_report(task, "block")

    print(f"{task['id']} blocked: {args.reason}")
    print_chat_title(task)
    return 0


def cmd_unblock(args: argparse.Namespace) -> int:
    task = find_task_or_current(args.task_id)
    if task["status"] != STATUS_BLOCKED:
        raise SystemExit(
            f"Task {task['id']} nao esta bloqueada (status atual: {task['status']})."
        )

    task["status"] = STATUS_IN_DEVELOPMENT
    blocks = task.get("blocks") or []
    if blocks and "unblockedAt" not in blocks[-1]:
        blocks[-1]["unblockedAt"] = today()
    note = f"Desbloqueada em {today()}."
    if args.note:
        note = f"Desbloqueada em {today()}: {args.note}"
    merge_list(task, "summary", [note])

    save_task(task)
    set_current_task(task)
    upsert_features_entry(task)
    write_report(task, "unblock")

    print(f"{task['id']} unblocked.")
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


def _is_dev_repo() -> bool:
    """True when running from the repo-mae (has core/manifest/).

    In the consumer (.ai-process/bin/ flat layout), core/ does not exist;
    the extended checks degrade to "lite" mode (just .ai/ files + git).
    """
    return (ROOT / "core" / "manifest").is_dir()


def cmd_doctor(args: argparse.Namespace) -> int:
    """Saude do pack. Endereca achado 2.10 da auditoria F-014.

    Modo dev (repo-mae, detectado via core/manifest/):
      1. .ai/ files existem
      2. core/manifest/manifest.yaml carrega como YAML valido
      3. PyYAML disponivel
      4. git no PATH (warn, nao fatal)
      5. render --check OK (a menos que --skip-render)
      6. dist/bin/ai.py existe
      7. lock_api.py importavel

    Modo consumer (layout flat .ai-process/bin/):
      1. .ai/ files existem
      4. git no PATH (warn)

    `--strict` promove warnings a erros tambem.
    """
    from _git_ops import has_git

    failures: list[str] = []
    warnings: list[str] = []

    # 1. .ai/ files (sempre)
    required = [PROCESS_FILE, TASKS_FILE, BACKLOG_FILE, CURRENT_FILE]
    for path in required:
        if not path.exists():
            failures.append(f"missing: {relative(path)}")

    # 4. git (sempre)
    if not has_git():
        warnings.append("git nao encontrado no PATH (commit/worktree falharao)")

    if _is_dev_repo():
        # 2 + 3. manifest + PyYAML
        manifest = ROOT / "core" / "manifest" / "manifest.yaml"
        if not manifest.exists():
            failures.append(f"missing: {relative(manifest)}")
        else:
            try:
                import yaml  # type: ignore

                data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
                if not isinstance(data, dict) or not data.get("verbs"):
                    failures.append(f"manifest invalido: {relative(manifest)} sem `verbs`")
            except ImportError:
                failures.append("PyYAML ausente: pip install pyyaml")
            except Exception as exc:
                failures.append(f"manifest YAML invalido: {exc}")

        # 5. render --check
        if not getattr(args, "skip_render", False):
            render = ROOT / "core" / "build" / "render-skills.py"
            if render.exists():
                import subprocess

                result = subprocess.run(
                    [sys.executable, str(render), "--check"],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    failures.append(
                        "render --check falhou: dist/ stale. Rode `python core/build/render-skills.py`"
                    )

        # 6. dist/bin/ai.py
        dist_ai = ROOT / "dist" / "bin" / "ai.py"
        if not dist_ai.exists():
            warnings.append(f"motor standalone ausente: {relative(dist_ai)}")

        # 7. lock_api importavel
        lock_api_path = ROOT / "core" / "lock" / "lock_api.py"
        if not lock_api_path.exists():
            failures.append(f"missing: {relative(lock_api_path)}")
        else:
            try:
                import importlib.util

                mod_name = "_doctor_lock_api_probe"
                spec = importlib.util.spec_from_file_location(mod_name, lock_api_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    # Python 3.13 + @dataclass exigem o modulo em sys.modules
                    # antes de executar (dataclass resolve tipos via
                    # sys.modules[cls.__module__]).
                    sys.modules[mod_name] = module
                    try:
                        spec.loader.exec_module(module)
                        for name in ("add_lock", "remove_lock", "find_blocked", "LockSpec"):
                            if not hasattr(module, name):
                                failures.append(f"lock_api sem `{name}`")
                    finally:
                        sys.modules.pop(mod_name, None)
            except Exception as exc:
                failures.append(f"lock_api falhou ao importar: {exc}")

    if getattr(args, "strict", False) and warnings:
        failures.extend(warnings)
        warnings = []

    for w in warnings:
        print(f"warn: {w}", file=sys.stderr)
    for f in failures:
        print(f"FAIL: {f}", file=sys.stderr)

    if failures:
        return 1
    print(MSG_PROCESS_FILES_OK)
    return 0


__all__ = [
    "cmd_init",
    "cmd_status",
    "cmd_ready",
    "cmd_finish",
    "cmd_cancel",
    "cmd_block",
    "cmd_unblock",
    "cmd_validate",
    "cmd_doctor",
]
