"""CLI handlers: feature / issue / backlog / promote.

Handles task creation and backlog -> task promotion. ADR-0011 Fase 2:
`backlog add` agora cria a entrada em `tasks.json` com `status=Backlog`
(ID neutro `D-NNN`). `backlog.json` legacy permanece read-only - itens
antigos (`B-NNN`) continuam visiveis em `backlog list` e promoveis via
`promote`, mas nenhuma escrita nova vai pra ele. `backlog migrate` copia
B-NNN legacy para tasks.json preservando ID.

Fix vs o monolitico ai.py:
- cmd_promote (achado 2.2): build the task FIRST, only persist disk
  mutation AFTER. Old code popped+wrote backlog before creating task;
  failure mid-way silently lost the item.
"""

from __future__ import annotations

import argparse
from typing import Any

from _clock import today
from _constants import (
    BACKLOG_FILE,
    KIND_FEATURE,
    MSG_BACKLOG_ITEM_NOT_FOUND,
    STATUS_BACKLOG,
    STATUS_IN_DEVELOPMENT,
    STATUS_PLANNED,
    TASKS_FILE,
)


# Mapping CLI -> status interno. Mantem o vocabulario do parser amigavel
# (in-development com hifen, planned sem acento) e isola a constante.
_STATUS_FROM_CLI = {
    "backlog": STATUS_BACKLOG,
    "planned": STATUS_PLANNED,
    "in-development": STATUS_IN_DEVELOPMENT,
}
STATUS_CLI_CHOICES = tuple(_STATUS_FROM_CLI.keys())
from _features_md import upsert_features_entry
from _state import read_json, write_json
from _tasks import (
    kind_marker,
    list_tasks,
    merge_list,
    new_task,
    next_task_id,
    pop_item,
    print_task_created,
    set_current_task,
)
from _worktree import attach_worktree


def cmd_create_task(args: argparse.Namespace, kind: str) -> int:
    """Cria uma task. ADR-0011 Fase 3: aceita `--status backlog|planned|
    in-development` (default in-development). Backlog nao entra em
    FEATURES.md (consistente com cmd_backlog_add); Planejada e
    Em desenvolvimento entram."""
    status_cli = getattr(args, "status", "in-development") or "in-development"
    status = _STATUS_FROM_CLI.get(status_cli, STATUS_IN_DEVELOPMENT)
    data = read_json(TASKS_FILE, {"schemaVersion": 1, "tasks": []})
    task_id = next_task_id(kind, data.get("tasks", []))
    task = new_task(task_id, kind, args.title, args.context, args.origin, status=status)
    data.setdefault("tasks", []).insert(0, task)
    write_json(TASKS_FILE, data)
    set_current_task(task)
    if status != STATUS_BACKLOG:
        upsert_features_entry(task)
    print_task_created(task)
    return 0


def cmd_backlog_add(args: argparse.Namespace) -> int:
    """Cria uma task com `status=Backlog` em tasks.json (ADR-0011 Fase 2).

    Nao escreve em backlog.json. Nao chama upsert_features_entry - itens
    em backlog ficam de fora do catalogo de FEATURES.md ate serem
    promovidos (cmd_promote ou ai start).
    """
    data = read_json(TASKS_FILE, {"schemaVersion": 1, "tasks": []})
    task_id = next_task_id(KIND_FEATURE, data.get("tasks", []))
    task = new_task(
        task_id,
        KIND_FEATURE,
        args.title,
        args.context,
        f"Backlog ({today()})",
        status=STATUS_BACKLOG,
    )
    data.setdefault("tasks", []).insert(0, task)
    write_json(TASKS_FILE, data)
    print(f"{task_id} added to backlog: {args.title}")
    return 0


def cmd_backlog_list(_args: argparse.Namespace) -> int:
    """Lista todo o backlog: tasks com status=Backlog em tasks.json +
    itens legacy em backlog.json (B-NNN)."""
    # Novas entradas (ADR-0011 Fase 2): tasks.json com status=Backlog.
    backlog_tasks = list_tasks(status=STATUS_BACKLOG)
    for task in backlog_tasks:
        marker = kind_marker(task.get("kind", ""))
        print(f"{task['id']} {marker} [Backlog] {task['title']}")

    # Legacy: backlog.json (B-NNN). Permanece read-only ate `backlog migrate`.
    # Itens legacy nao tem `kind` salvo - usa fallback do marker.
    legacy = read_json(BACKLOG_FILE, {"schemaVersion": 1, "items": []})
    for item in legacy.get("items", []):
        marker = kind_marker(item.get("kind", ""))
        print(f"{item['id']} {marker} [{item['status']}] {item['title']}")
    return 0


def cmd_backlog_migrate(args: argparse.Namespace) -> int:
    """Move itens legacy de backlog.json para tasks.json preservando ID.

    Por default e dry-run: lista o que seria migrado sem escrever. Com
    `--force` aplica: cada item B-NNN vira uma task com mesmo id,
    `status=Backlog`, `kind=feature`. backlog.json e esvaziado apos
    migracao com sucesso. Idempotente: se um id ja existe em tasks.json,
    pula (avisa no stderr).
    """
    legacy = read_json(BACKLOG_FILE, {"schemaVersion": 1, "items": []})
    items = legacy.get("items", [])
    if not items:
        print("Nenhum item legacy em backlog.json para migrar.")
        return 0

    tasks_data = read_json(TASKS_FILE, {"schemaVersion": 1, "tasks": []})
    existing_ids = {task.get("id") for task in tasks_data.get("tasks", [])}

    to_migrate: list[dict[str, Any]] = []
    skipped: list[str] = []
    for item in items:
        if item.get("id") in existing_ids:
            skipped.append(item["id"])
            continue
        to_migrate.append(item)

    if args.dry_run or not args.force:
        print(
            f"dry-run: {len(to_migrate)} item(s) seriam migrados; "
            f"{len(skipped)} ja em tasks.json (pulariam)."
        )
        for item in to_migrate:
            print(f"  + {item['id']} -> tasks.json (status=Backlog, kind={KIND_FEATURE})")
        for sid in skipped:
            print(f"  ~ {sid} ja presente em tasks.json, pulado")
        print("\nUse --force para aplicar.")
        return 0

    for item in to_migrate:
        task = new_task(
            item["id"],
            KIND_FEATURE,
            item.get("title", ""),
            item.get("context", ""),
            f"Backlog legacy migrado ({today()})",
            status=STATUS_BACKLOG,
        )
        # Preservar createdAt original do backlog item, se houver.
        if item.get("createdAt"):
            task["createdAt"] = item["createdAt"]
        tasks_data.setdefault("tasks", []).insert(0, task)

    write_json(TASKS_FILE, tasks_data)
    legacy["items"] = []
    write_json(BACKLOG_FILE, legacy)

    print(
        f"Migrados {len(to_migrate)} item(s) para tasks.json (status=Backlog). "
        f"{len(skipped)} pulado(s) (id ja em tasks.json). "
        f"backlog.json esvaziado."
    )
    return 0


def _find_backlog_source(
    backlog_id: str,
) -> tuple[str, dict[str, Any]] | None:
    """Localiza um item de backlog em tasks.json (status=Backlog) ou
    backlog.json legacy. Retorna (source, item) onde source e 'tasks' ou
    'legacy', ou None se nao achar.
    """
    for task in list_tasks(status=STATUS_BACKLOG):
        if task.get("id") == backlog_id:
            return ("tasks", task)
    legacy = read_json(BACKLOG_FILE, {"schemaVersion": 1, "items": []})
    for item in legacy.get("items", []):
        if item.get("id") == backlog_id:
            return ("legacy", item)
    return None


def _promoted_summary(args: argparse.Namespace, source_id: str) -> list[str]:
    summary: list[str] = [f"Backlog {source_id} promovido via guia-fluxo."]
    if args.assessment:
        summary.append(f"Avaliacao IA: {args.assessment[0]}")
    return summary


def _new_promoted_task(
    args: argparse.Namespace, item: dict[str, Any]
) -> dict[str, Any]:
    """Cria uma task em desenvolvimento a partir de um item de backlog
    legacy (backlog.json). ID novo D-NNN; preserva backlogId original."""
    data = read_json(TASKS_FILE, {"schemaVersion": 1, "tasks": []})
    task_id = next_task_id(args.kind, data.get("tasks", []))
    title = args.title or f"{item['id']}: {item['title']}"
    context = args.context or f"Backlog {item['id']}: {item.get('context') or item['title']}"
    task = new_task(
        task_id,
        args.kind,
        title,
        context,
        f"Backlog {item['id']} ({today()})",
    )
    task["backlogId"] = item["id"]
    task["assessment"] = args.assessment
    task["executionPlan"] = args.plan
    task["summary"] = _promoted_summary(args, item["id"])
    if args.plan:
        merge_list(task, "pending", ["Executar plano aprovado antes da implementacao."])
    return task


def _promote_existing_task(
    args: argparse.Namespace, task: dict[str, Any]
) -> dict[str, Any]:
    """Promove uma task ja em tasks.json (status=Backlog) para
    Em desenvolvimento (ADR-0011 Fase 2). Preserva o id."""
    task["status"] = STATUS_IN_DEVELOPMENT
    task["kind"] = args.kind
    task["updatedAt"] = today()
    if args.title:
        task["title"] = args.title
    if args.context:
        task["context"] = args.context
    task["origin"] = f"Backlog {task['id']} promovido ({today()})"
    task["assessment"] = args.assessment
    task["executionPlan"] = args.plan
    task["modifiedFiles"] = list(set(task.get("modifiedFiles", []) + ["FEATURES.md"]))
    merge_list(task, "summary", _promoted_summary(args, task["id"]))
    if args.plan:
        merge_list(task, "pending", ["Executar plano aprovado antes da implementacao."])
    return task


def cmd_promote(args: argparse.Namespace) -> int:
    found = _find_backlog_source(args.backlog_id)
    if found is None:
        raise SystemExit(MSG_BACKLOG_ITEM_NOT_FOUND.format(id=args.backlog_id))

    source, item = found
    if source == "tasks":
        # Build task in-place no tasks.json (preserva ID original).
        task = _promote_existing_task(args, item)
        if args.worktree:
            attach_worktree(task, args, item)

        # Re-escreve tasks.json com a task mutada.
        tasks_data = read_json(TASKS_FILE, {"schemaVersion": 1, "tasks": []})
        for idx, existing in enumerate(tasks_data.get("tasks", [])):
            if existing.get("id") == task["id"]:
                tasks_data["tasks"][idx] = task
                break
        write_json(TASKS_FILE, tasks_data)
    else:
        # Legacy: cria task nova com D-NNN e remove de backlog.json.
        task = _new_promoted_task(args, item)
        if args.worktree:
            attach_worktree(task, args, item)

        legacy = read_json(BACKLOG_FILE, {"schemaVersion": 1, "items": []})
        pop_item(legacy.get("items", []), args.backlog_id)
        write_json(BACKLOG_FILE, legacy)

        tasks_data = read_json(TASKS_FILE, {"schemaVersion": 1, "tasks": []})
        tasks_data.setdefault("tasks", []).insert(0, task)
        write_json(TASKS_FILE, tasks_data)

    set_current_task(task)
    upsert_features_entry(task)
    print_task_created(task)
    if task.get("worktree", {}).get("path"):
        print(f"WORKTREE_PATH={task['worktree']['path']}")
    return 0


__all__ = [
    "cmd_create_task",
    "cmd_backlog_add",
    "cmd_backlog_list",
    "cmd_backlog_migrate",
    "cmd_promote",
    "STATUS_CLI_CHOICES",
]
