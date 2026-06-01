#!/usr/bin/env python3
"""Portable AI-process CLI for agents and humans.

Usage examples:
    python scripts/ai.py feature "Nova tela de revisao"
    python scripts/ai.py issue "Filtro quebra no endpoint"
    python scripts/ai.py backlog add "Ideia futura"
    python scripts/ai.py ready F-016 --file scripts/ai.py
    python scripts/ai.py finish F-016 --lock --lock-id ai-process-pack
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
AI_DIR = ROOT / ".ai"
PROCESS_FILE = AI_DIR / "process.json"
TASKS_FILE = AI_DIR / "tasks.json"
BACKLOG_FILE = AI_DIR / "backlog.json"
CURRENT_FILE = AI_DIR / "current-task.json"
CHAT_TITLE_FILE = AI_DIR / "chat-title.txt"
DOCS_MAP_FILE = AI_DIR / "docs-map.yaml"
REPORTS_DIR = AI_DIR / "reports"
FEATURES_FILE = ROOT / "FEATURES.md"

TASK_HEADING_RE = re.compile(r"^## \[([FI])-(\d+)\] (.+)$", re.MULTILINE)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Portable AI process commands.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Create .ai process files for this repo.")
    p_init.add_argument("--project-name", default=ROOT.name)
    p_init.add_argument("--force", action="store_true")
    p_init.set_defaults(func=cmd_init)

    p_feature = sub.add_parser("feature", help="Create a feature task.")
    add_task_args(p_feature)
    p_feature.set_defaults(func=lambda args: cmd_create_task(args, "feature"))

    p_issue = sub.add_parser("issue", help="Create an issue task.")
    add_task_args(p_issue)
    p_issue.set_defaults(func=lambda args: cmd_create_task(args, "issue"))

    p_status = sub.add_parser("status", help="Show current task or a given task.")
    p_status.add_argument("task_id", nargs="?")
    p_status.set_defaults(func=cmd_status)

    p_ready = sub.add_parser("ready", help="Move task to developer validation stage.")
    p_ready.add_argument("task_id", nargs="?")
    p_ready.add_argument("--file", action="append", default=[])
    p_ready.add_argument("--summary", action="append", default=[])
    p_ready.add_argument("--validation", action="append", default=[])
    p_ready.add_argument("--pending", action="append", default=[])
    p_ready.add_argument("--run-tests", action="store_true")
    p_ready.set_defaults(func=cmd_ready)

    p_finish = sub.add_parser("finish", help="Close an already validated task.")
    p_finish.add_argument("task_id", nargs="?")
    p_finish.add_argument("--file", action="append", default=[])
    p_finish.add_argument("--summary", action="append", default=[])
    p_finish.add_argument("--validation", action="append", default=[])
    p_finish.add_argument("--pending", action="append", default=[])
    p_finish.add_argument("--run-tests", action="store_true")
    p_finish.add_argument("--commit", action=argparse.BooleanOptionalAction, default=None)
    p_finish.add_argument("--lock", action="store_true")
    p_finish.add_argument("--lock-id")
    p_finish.add_argument("--lock-description")
    p_finish.add_argument(
        "--docs-touched",
        action="append",
        default=[],
        help="Doc atualizado durante esta finalizacao. Repetir por arquivo.",
    )
    p_finish.add_argument(
        "--docs-skip",
        help="Justificativa quando nenhum doc precisou ser atualizado.",
    )
    p_finish.add_argument(
        "--docs-checked",
        action="store_true",
        help="Confirmacao explicita de que os docs foram revisados (use junto com --docs-touched ou --docs-skip).",
    )
    p_finish.set_defaults(func=cmd_finish)

    p_docs_check = sub.add_parser(
        "docs-check",
        help="Lista docs candidatos a atualizacao para a task atual (le .ai/docs-map.yaml).",
    )
    p_docs_check.add_argument("task_id", nargs="?")
    p_docs_check.add_argument(
        "--json",
        action="store_true",
        help="Saida em JSON para consumo por agente.",
    )
    p_docs_check.set_defaults(func=cmd_docs_check)

    p_validate = sub.add_parser("validate", help="Deprecated alias: mark task as validated without committing.")
    p_validate.add_argument("task_id", nargs="?")
    p_validate.add_argument("--file", action="append", default=[])
    p_validate.add_argument("--summary", action="append", default=[])
    p_validate.add_argument("--lock-id")
    p_validate.add_argument("--lock-description")
    p_validate.add_argument("--lock", action="store_true")
    p_validate.set_defaults(func=cmd_validate)

    p_backlog = sub.add_parser("backlog", help="Manage future work.")
    backlog_sub = p_backlog.add_subparsers(dest="backlog_command", required=True)
    p_backlog_add = backlog_sub.add_parser("add", help="Add backlog item.")
    p_backlog_add.add_argument("title")
    p_backlog_add.add_argument("--context", default="")
    p_backlog_add.set_defaults(func=cmd_backlog_add)
    p_backlog_list = backlog_sub.add_parser("list", help="List backlog items.")
    p_backlog_list.set_defaults(func=cmd_backlog_list)
    p_backlog_promote = backlog_sub.add_parser("promote", help="Promote backlog item.")
    p_backlog_promote.add_argument("backlog_id")
    p_backlog_promote.add_argument("--kind", choices=["feature", "issue"], default="feature")
    add_promote_args(p_backlog_promote)
    p_backlog_promote.set_defaults(func=cmd_promote)

    p_promote = sub.add_parser("promote", help="Promote a backlog item to feature or issue.")
    p_promote.add_argument("backlog_id")
    p_promote.add_argument("--kind", choices=["feature", "issue"], required=True)
    add_promote_args(p_promote)
    p_promote.set_defaults(func=cmd_promote)

    p_doctor = sub.add_parser("doctor", help="Check process files.")
    p_doctor.set_defaults(func=cmd_doctor)

    p_render = sub.add_parser("render", help="Render per-agent skill/command files from skills/manifest.yaml.")
    p_render.add_argument("--check", action="store_true", help="Exit 1 se algum alvo gerado estiver stale.")
    p_render.add_argument("--verb", help="Renderiza apenas um verbo do manifest.")
    p_render.set_defaults(func=cmd_render)

    return parser


def add_task_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("title")
    parser.add_argument("--context", default="")
    parser.add_argument("--origin", default=f"AI process ({today()})")


def add_promote_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--title")
    parser.add_argument("--context")
    parser.add_argument("--assessment", action="append", default=[])
    parser.add_argument("--plan", action="append", default=[])
    parser.add_argument("--worktree", action="store_true")
    parser.add_argument("--worktree-path")
    parser.add_argument("--branch")
    parser.add_argument("--create-worktree", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--remove-worktree-on-finish", action=argparse.BooleanOptionalAction, default=True)


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


def cmd_create_task(args: argparse.Namespace, kind: str) -> int:
    data = read_json(TASKS_FILE, {"schemaVersion": 1, "tasks": []})
    task_id = next_task_id(kind, data.get("tasks", []))
    task = new_task(task_id, kind, args.title, args.context, args.origin)
    data.setdefault("tasks", []).insert(0, task)
    write_json(TASKS_FILE, data)
    set_current_task(task)
    upsert_features_entry(task)
    print_task_created(task)
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    task = find_task_or_current(args.task_id)
    print(json.dumps(task, ensure_ascii=False, indent=2))
    print_chat_title(task)
    return 0


def cmd_ready(args: argparse.Namespace) -> int:
    task = find_task_or_current(args.task_id)
    config = read_json(PROCESS_FILE, default_process(ROOT.name))
    changed_files = args.file or git_changed_files()
    task["status"] = config.get("ready", {}).get("status", "Aguardando validacao")
    merge_list(task, "modifiedFiles", changed_files)
    merge_list(task, "summary", args.summary or ["Implementacao entregue para validacao via ai-process."])
    merge_list(task, "validations", args.validation)
    task["pending"] = args.pending or ["Validacao manual do desenvolvedor."]

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
    task["status"] = finish_config.get("status", "Validada")
    merge_list(task, "modifiedFiles", changed_files)
    merge_list(task, "modifiedFiles", args.docs_touched)
    merge_list(task, "summary", args.summary or ["Demanda finalizada via ai-process."])
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
    cleanup_task_worktree(task, commit_requested)

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
    task = find_task_or_current(args.task_id)
    config = read_json(PROCESS_FILE, default_process(ROOT.name))
    task["status"] = config.get("validate", {}).get("status", "Validada")
    merge_list(task, "modifiedFiles", args.file)
    merge_list(task, "summary", args.summary or ["Validacao confirmada pelo desenvolvedor."])
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


def cmd_backlog_add(args: argparse.Namespace) -> int:
    data = read_json(BACKLOG_FILE, {"schemaVersion": 1, "items": []})
    item_id = next_backlog_id(data.get("items", []))
    item = {
        "id": item_id,
        "title": args.title,
        "context": args.context,
        "status": "Backlog",
        "createdAt": today(),
        "updatedAt": today(),
    }
    data.setdefault("items", []).insert(0, item)
    write_json(BACKLOG_FILE, data)
    print(f"{item_id} added to backlog: {args.title}")
    return 0


def cmd_backlog_list(_args: argparse.Namespace) -> int:
    data = read_json(BACKLOG_FILE, {"schemaVersion": 1, "items": []})
    for item in data.get("items", []):
        print(f"{item['id']} [{item['status']}] {item['title']}")
    return 0


def cmd_promote(args: argparse.Namespace) -> int:
    backlog = read_json(BACKLOG_FILE, {"schemaVersion": 1, "items": []})
    item = pop_item(backlog.get("items", []), args.backlog_id)
    if item is None:
        raise SystemExit(f"Backlog item not found: {args.backlog_id}")
    write_json(BACKLOG_FILE, backlog)
    task = create_promoted_task(args, item)
    if args.worktree:
        attach_worktree(task, args, item)
    data = read_json(TASKS_FILE, {"schemaVersion": 1, "tasks": []})
    data.setdefault("tasks", []).insert(0, task)
    write_json(TASKS_FILE, data)
    set_current_task(task)
    upsert_features_entry(task)
    print_task_created(task)
    if task.get("worktree", {}).get("path"):
        print(f"WORKTREE_PATH={task['worktree']['path']}")
    return 0


def create_promoted_task(args: argparse.Namespace, item: dict[str, Any]) -> dict[str, Any]:
    data = read_json(TASKS_FILE, {"schemaVersion": 1, "tasks": []})
    task_id = next_task_id(args.kind, data.get("tasks", []))
    title = args.title or f"{item['id']}: {item['title']}"
    context = args.context or f"Backlog {item['id']}: {item.get('context') or item['title']}"
    task = new_task(task_id, args.kind, title, context, f"Backlog {item['id']} ({today()})")
    task["backlogId"] = item["id"]
    task["assessment"] = args.assessment
    task["executionPlan"] = args.plan
    task["summary"] = ["Backlog promovido via ai-process."]
    if args.assessment:
        merge_list(task, "summary", [f"Avaliacao IA: {args.assessment[0]}"])
    if args.plan:
        merge_list(task, "pending", ["Executar plano aprovado antes da implementacao."])
    return task


def attach_worktree(task: dict[str, Any], args: argparse.Namespace, item: dict[str, Any]) -> None:
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
    absolute_path = ROOT / path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(git_command("worktree", "add", "-b", branch, str(absolute_path)), cwd=ROOT, check=True)
    task["worktree"]["created"] = True


def cmd_doctor(_args: argparse.Namespace) -> int:
    missing = [path for path in [PROCESS_FILE, TASKS_FILE, BACKLOG_FILE, CURRENT_FILE] if not path.exists()]
    if missing:
        for path in missing:
            print(f"missing: {relative(path)}")
        return 1
    print("AI process files OK.")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    render_script = ROOT / "scripts" / "render-skills.py"
    if not render_script.exists():
        print(f"missing: {relative(render_script)}", file=sys.stderr)
        return 2
    cmd = [sys.executable, str(render_script)]
    if args.check:
        cmd.append("--check")
    if args.verb:
        cmd.extend(["--verb", args.verb])
    return subprocess.call(cmd)


def default_process(project_name: str) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "name": "ai-process",
        "projectName": project_name,
        "ids": {"featurePrefix": "F", "issuePrefix": "I", "backlogPrefix": "B", "digits": 3},
        "chatTitleFormat": "{id} - #{statusTag} - {title}",
        "ready": {
            "status": "Aguardando validacao",
            "runValidationByDefault": False,
            "validationCommands": [],
        },
        "finish": {
            "status": "Validada",
            "runValidationByDefault": False,
            "validationCommands": [],
            "commitByDefault": True,
            "lockOnFinish": False,
        },
        "validate": {
            "status": "Validada",
            "deprecatedAliasFor": "finish --no-commit",
            "lockOnValidate": False,
        },
    }


def new_task(task_id: str, kind: str, title: str, context: str, origin: str) -> dict[str, Any]:
    return {
        "id": task_id,
        "kind": kind,
        "title": title,
        "status": "Em desenvolvimento",
        "origin": origin,
        "context": context or title,
        "createdAt": today(),
        "updatedAt": today(),
        "modifiedFiles": ["FEATURES.md"],
        "summary": ["Demanda criada via ai-process."],
        "validations": [],
        "pending": ["Executar implementacao e validacoes."],
    }


def next_task_id(kind: str, tasks: list[dict[str, Any]]) -> str:
    prefix = "F" if kind == "feature" else "I"
    numbers = [number_from_id(task.get("id", ""), prefix) for task in tasks]
    numbers.extend(numbers_from_features(prefix))
    next_number = max([n for n in numbers if n is not None], default=0) + 1
    return f"{prefix}-{next_number:03d}"


def next_backlog_id(items: list[dict[str, Any]]) -> str:
    numbers = [number_from_id(item.get("id", ""), "B") for item in items]
    next_number = max([n for n in numbers if n is not None], default=0) + 1
    return f"B-{next_number:03d}"


def number_from_id(value: str, prefix: str) -> int | None:
    match = re.fullmatch(rf"{prefix}-(\d+)", value or "")
    return int(match.group(1)) if match else None


def numbers_from_features(prefix: str) -> list[int]:
    if not FEATURES_FILE.exists():
        return []
    return [
        int(match.group(2))
        for match in TASK_HEADING_RE.finditer(read_text(FEATURES_FILE))
        if match.group(1) == prefix
    ]


def find_task_or_current(task_id: str | None) -> dict[str, Any]:
    current = read_json(CURRENT_FILE, {})
    chosen_id = task_id or current.get("taskId")
    if not chosen_id:
        raise SystemExit("No task id provided and no current task set.")
    task = find_task(chosen_id)
    if task is None:
        raise SystemExit(f"Task not found: {chosen_id}")
    return task


def find_task(task_id: str) -> dict[str, Any] | None:
    data = read_json(TASKS_FILE, {"tasks": []})
    return next((task for task in data.get("tasks", []) if task.get("id") == task_id), None)


def save_task(updated: dict[str, Any]) -> None:
    data = read_json(TASKS_FILE, {"schemaVersion": 1, "tasks": []})
    for index, task in enumerate(data.get("tasks", [])):
        if task.get("id") == updated.get("id"):
            updated["updatedAt"] = today()
            data["tasks"][index] = updated
            write_json(TASKS_FILE, data)
            return
    raise SystemExit(f"Task not found: {updated.get('id')}")


def pop_item(items: list[dict[str, Any]], item_id: str) -> dict[str, Any] | None:
    for index, item in enumerate(items):
        if item.get("id") == item_id:
            return items.pop(index)
    return None


def merge_list(task: dict[str, Any], key: str, values: list[str]) -> None:
    current = list(task.get(key, []))
    for value in values:
        if value and value not in current:
            current.append(value)
    task[key] = current


def upsert_features_entry(task: dict[str, Any]) -> None:
    if not FEATURES_FILE.exists():
        FEATURES_FILE.write_text("# Features e Issues\n\n---\n\n", encoding="utf-8")
    content = read_text(FEATURES_FILE)
    block = render_features_block(task)
    pattern = re.compile(rf"^## \[{re.escape(task['id'])}\].*?(?=^## \[[FI]-\d+\] |\Z)", re.MULTILINE | re.DOTALL)
    if pattern.search(content):
        # Lambda: trata block como literal (re.sub interpreta \X em strings repl,
        # quebrando em paths Windows como `src\editor\...` -> bad escape \e).
        content = pattern.sub(lambda _match: block, content)
    else:
        marker = "---\n\n"
        insert_at = content.find(marker)
        if insert_at >= 0:
            insert_at += len(marker)
            content = content[:insert_at] + block + "\n" + content[insert_at:]
        else:
            content = content.rstrip() + "\n\n" + block
    FEATURES_FILE.write_text(content, encoding="utf-8")


def render_features_block(task: dict[str, Any]) -> str:
    lines = [
        f"## [{task['id']}] {task['title']}",
        "",
        f"- **Status:** {task['status']}",
        f"- **Origem:** {task.get('origin', 'AI process')}",
        f"- **Tipo:** {task_kind_label(task)}",
        f"- **Contexto:** {task.get('context', task['title'])}",
        "",
        "### Arquivos modificados/criados",
        "",
    ]
    lines.extend(markdown_list(task.get("modifiedFiles", []), "`"))
    lines.extend(["", "### O que foi feito", ""])
    lines.extend(markdown_list(task.get("summary", [])))
    lines.extend(["", "### Validacao feita", ""])
    lines.extend(markdown_list(task.get("validations", [])))
    lines.extend(["", "### Validacao pendente", ""])
    lines.extend(markdown_list(task.get("pending", [])))
    lines.append("")
    lines.append("")
    return "\n".join(lines)


def markdown_list(values: list[str], wrap: str = "") -> list[str]:
    if not values:
        return ["- Nenhuma."]
    return [f"- {wrap}{value}{wrap}" for value in values]


def task_kind_label(task: dict[str, Any]) -> str:
    return "Feature" if task.get("kind") == "feature" else "Issue / regressao"


def run_validation_commands(task: dict[str, Any], config: dict[str, Any], section: str) -> None:
    commands = config.get(section, {}).get("validationCommands", [])
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, shell=True, text=True)
        status = "OK" if result.returncode == 0 else f"falhou ({result.returncode})"
        merge_list(task, "validations", [f"{command} - {status}"])
        if result.returncode != 0:
            raise SystemExit(result.returncode)


def commit_task(task: dict[str, Any]) -> None:
    files = [value for value in task.get("modifiedFiles", []) if value != "Nenhuma."]
    if not files:
        raise SystemExit("No files registered for commit.")
    unexpected = sorted(set(git_staged_files()) - set(files))
    if unexpected:
        names = ", ".join(unexpected)
        raise SystemExit(f"Unrelated staged files would be committed: {names}")
    subprocess.run(git_command("add", "--", *files), cwd=ROOT, check=True)
    message = f"{task['kind']}: {task['title']}\n\nTask: {task['id']}"
    subprocess.run(git_command("commit", "-m", message), cwd=ROOT, check=True)


def cleanup_task_worktree(task: dict[str, Any], commit_requested: bool) -> None:
    worktree = task.get("worktree") or {}
    if not worktree.get("enabled") or not worktree.get("removeOnFinish"):
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
        return
    command = git_command("worktree", "remove", str(absolute_path))
    if commit_requested:
        command.append("--force")
    subprocess.run(command, cwd=ROOT, check=True)
    worktree["removedAt"] = today()
    worktree["created"] = False


def lock_task_files(task: dict[str, Any], lock_id: str | None, description: str | None) -> None:
    files = [
        value
        for value in task.get("modifiedFiles", [])
        if value not in {"FEATURES.md", "features/registry.yaml", "Nenhuma."}
    ]
    if not lock_id:
        raise SystemExit("--lock-id is required when using --lock.")
    if not files:
        raise SystemExit("No files to lock. Add files with --file.")
    registry = ROOT / "features" / "registry.yaml"
    registry.parent.mkdir(exist_ok=True)
    if registry.exists():
        content = registry.read_text(encoding="utf-8")
    else:
        content = (
            "# Veja features/README.md para o protocolo e formato.\n"
            "# Edicao via CLI (recomendado): python bin/check-lock.py lock|unlock\n"
            "# Ou edite manualmente preservando o schema abaixo.\n\n"
            "version: 1\nlocks:\n"
        )
    if re.search(rf"^\s*-\s*id:\s*{re.escape(lock_id)}\s*$", content, re.MULTILINE):
        raise SystemExit(f"Lock already exists: {lock_id}")
    if "locks:" not in content:
        content = content.rstrip() + "\nlocks:\n"
    block = [
        f"- id: {lock_id}",
        f"  description: {yaml_string(description or task['title'])}",
        f"  locked_at: {today()}",
        "  files:",
    ]
    block.extend(f"  - {yaml_string(file_path)}" for file_path in files)
    registry.write_text(content.rstrip() + "\n" + "\n".join(block) + "\n", encoding="utf-8")


def git_changed_files() -> list[str]:
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


# --- Docs hook (F-010) -------------------------------------------------------

def load_docs_map() -> dict[str, Any] | None:
    """Carrega .ai/docs-map.yaml. Retorna None se nao existir."""
    if not DOCS_MAP_FILE.exists():
        return None
    try:
        import yaml  # type: ignore
    except ImportError:
        sys.stderr.write(
            "docs-check: PyYAML nao instalado. Rode: pip install pyyaml\n"
        )
        return None
    data = yaml.safe_load(DOCS_MAP_FILE.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"{relative(DOCS_MAP_FILE)}: raiz precisa ser um mapping.")
    return data


def compute_docs_candidates(
    task: dict[str, Any],
    changed_files: list[str],
    docs_map: dict[str, Any],
) -> list[dict[str, str]]:
    """Aplica triggers do docs-map a uma task. Retorna lista de candidatos."""
    files = list(dict.fromkeys(task.get("modifiedFiles", []) + (changed_files or [])))
    files = [f for f in files if f and f != "Nenhuma."]

    candidates: list[dict[str, str]] = []
    for entry in docs_map.get("docs", []) or []:
        if not isinstance(entry, dict):
            continue
        path = entry.get("path")
        if not path:
            continue
        purpose = entry.get("purpose", "")
        for trigger in entry.get("triggers", []) or []:
            if not isinstance(trigger, dict):
                continue
            # `event` e o nome canonico. Aceitamos `on` para compat futura, mas
            # apenas quando vier como string (PyYAML/YAML 1.1 converte `on:`
            # nao-quotada em True; nesse caso ignoramos para nao mascarar bug).
            kind = trigger.get("event")
            if kind is None:
                raw_on = trigger.get("on")
                if isinstance(raw_on, str):
                    kind = raw_on
            hint = trigger.get("hint", "")
            reason = trigger_reason(kind, trigger, files, task)
            if reason is None:
                continue
            candidates.append(
                {
                    "path": path,
                    "trigger": kind or "",
                    "reason": reason,
                    "hint": hint,
                    "purpose": purpose,
                }
            )
            break  # uma entrada de doc gera no maximo 1 candidato
    return candidates


def trigger_reason(
    kind: str | None,
    trigger: dict[str, Any],
    files: list[str],
    task: dict[str, Any],
) -> str | None:
    """Retorna a razao de match, ou None se o trigger nao bate."""
    if kind == "task-finished":
        kind_label = "feature" if task.get("kind") == "feature" else "issue"
        return f"task-finished: {kind_label} {task.get('id')}"
    if kind == "touched":
        patterns = [p for p in (trigger.get("paths") or []) if p]
        matches = [f for f in files if any(fnmatch.fnmatch(f, p) for p in patterns)]
        if matches:
            joined = ", ".join(matches[:3])
            extra = "" if len(matches) <= 3 else f" (+{len(matches) - 3} outros)"
            return f"touched: {joined}{extra}"
        return None
    if kind == "architectural-decision":
        # Heuristica humana: agente decide. Sempre lista como candidato a avaliar.
        return "architectural-decision: avalie se a feature/issue mudou regra arquitetural"
    # Trigger desconhecido: silenciosamente ignora pra nao quebrar mapas futuros.
    return None


def ensure_docs_review_ok(
    task: dict[str, Any],
    changed_files: list[str],
    docs_map: dict[str, Any],
    args: argparse.Namespace,
) -> None:
    """Bloqueia o finish quando ha candidatos sem revisao registrada."""
    candidates = compute_docs_candidates(task, changed_files, docs_map)
    if not candidates:
        return
    touched = [t for t in (args.docs_touched or []) if t]
    skipped_reason = (args.docs_skip or "").strip()
    if not touched and not skipped_reason and not args.docs_checked:
        print_docs_block(task, candidates)
        raise SystemExit(
            "docs-check: revise os docs candidatos acima e rode novamente com "
            "--docs-touched <path> (pode repetir) ou --docs-skip \"<motivo>\". "
            "Use --docs-checked sozinho apenas se tem certeza de que nao ha nada a tocar."
        )


def build_docs_review_record(
    task: dict[str, Any],
    changed_files: list[str],
    docs_map: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    candidates = compute_docs_candidates(task, changed_files, docs_map)
    record = {
        "candidates": candidates,
        "touched": [t for t in (args.docs_touched or []) if t],
        "checkedAt": today(),
    }
    if args.docs_skip:
        record["skipped"] = args.docs_skip.strip()
    return record


def print_docs_block(task: dict[str, Any], candidates: list[dict[str, str]]) -> None:
    print()
    print(f"=== docs-check: {task.get('id')} ===")
    print(
        "Os docs abaixo foram listados como candidatos a atualizacao por causa "
        "desta demanda. Avalie cada um, atualize quando fizer sentido, e feche o "
        "finish registrando o que fez."
    )
    print()
    for candidate in candidates:
        print(f"- {candidate['path']}")
        if candidate.get("purpose"):
            print(f"    purpose: {candidate['purpose']}")
        print(f"    motivo:  {candidate['reason']}")
        if candidate.get("hint"):
            print(f"    hint:    {candidate['hint']}")
    print()
    print("Como prosseguir:")
    print("  - Atualizou alguns? Re-rode com --docs-touched <path> [--docs-touched ...].")
    print("  - Nenhum precisava? Re-rode com --docs-skip \"<motivo curto>\".")
    print("  - Misto e OK: --docs-touched A --docs-touched B --docs-skip \"...\".")


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


def write_report(task: dict[str, Any], event: str) -> None:
    REPORTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = REPORTS_DIR / f"{task['id']}-{event}-{stamp}.md"
    path.write_text(render_features_block(task), encoding="utf-8")


def print_task_created(task: dict[str, Any]) -> None:
    print(f"{task['id']} created: {task['title']}")
    print_chat_title(task)


def chat_title(task: dict[str, Any]) -> str:
    template = read_json(PROCESS_FILE, default_process(ROOT.name)).get(
        "chatTitleFormat",
        "{id} - #{statusTag} - {title}",
    )
    return template.format(id=task["id"], statusTag=status_tag(task["status"]), title=task["title"])


def status_tag(status: str) -> str:
    mapping = {
        "Em desenvolvimento": "DEV",
        "Aguardando validacao": "VALIDACAO",
        "Aguardando validação": "VALIDACAO",
        "Validada": "FINALIZADO",
        "Finalizada": "FINALIZADO",
        "Planejada": "PLANEJADA",
        "Bloqueada": "BLOQUEADA",
        "Cancelada": "CANCELADA",
    }
    return mapping.get(status, status.upper().replace(" ", "_"))


def current_task_payload(task: dict[str, Any]) -> dict[str, str]:
    return {
        "taskId": task["id"],
        "status": task["status"],
        "title": task["title"],
        "chatTitle": chat_title(task),
    }


def set_current_task(task: dict[str, Any]) -> None:
    write_json(CURRENT_FILE, current_task_payload(task))
    CHAT_TITLE_FILE.write_text(chat_title(task) + "\n", encoding="utf-8")


def print_chat_title(task: dict[str, Any]) -> None:
    print(f"\nNOME DO CHAT: {chat_title(task)}")
    print(f"CHAT_TITLE={chat_title(task)}")


def git_staged_files() -> list[str]:
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


def git_command(*args: str) -> list[str]:
    return ["git", "-c", f"safe.directory={ROOT.as_posix()}", *args]


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return cleaned[:80] or "task"


def write_if_missing(path: Path, payload: dict[str, Any], force: bool = False) -> None:
    if path.exists() and not force:
        return
    write_json(path, payload)


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def today() -> str:
    return date.today().isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
