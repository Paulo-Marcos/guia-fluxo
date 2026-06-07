#!/usr/bin/env python3
"""Portable AI-process CLI for agents and humans.

Entry point only. Each subcommand delegates to a handler under `_cli_*`.
Domain logic lives in `_tasks`, `_features_md`, `_docs_hook`, `_locks`,
`_worktree`, `_commit`. Persistence in `_state`. Git in `_git_ops`.
Constants/messages in `_constants`.

Usage examples:
    python core/src/ai.py feature "Nova tela de revisao"
    python core/src/ai.py issue "Filtro quebra no endpoint"
    python core/src/ai.py backlog add "Ideia futura"
    python core/src/ai.py ready F-016 --file core/src/ai.py
    python core/src/ai.py finish F-016 --lock --lock-id ai-process-pack
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _bootstrap_sys_path() -> None:
    """Ensure sibling modules (_constants, lock_api, ...) are importable.

    When invoked as a script (`python core/src/ai.py ...`), Python sets
    sys.path[0] to the script's directory automatically, so siblings in
    `core/src/` work. We additionally add `core/lock/` to support
    `import lock_api` in dev. In the dist/ layout everything is flat
    under dist/bin/ so this is a no-op.
    """
    here = Path(__file__).resolve().parent
    candidates = [here, here.parent / "lock"]
    for candidate in candidates:
        path_str = str(candidate)
        if candidate.exists() and path_str not in sys.path:
            sys.path.insert(0, path_str)


def _bootstrap_utf8_io() -> None:
    """Force stdout/stderr to UTF-8 so chat-title e listas com emoji
    (KIND_MARKERS, D-035) nao quebrem em consoles Windows cp1252.

    Python 3.7+ expoe `reconfigure` em TextIO streams; quando ausente
    (stream redirecionado para algo nao-reconfiguravel), engole o erro
    silenciosamente - o pior caso e voltar ao comportamento anterior.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


_bootstrap_sys_path()
_bootstrap_utf8_io()


from _clock import today  # noqa: E402
from _cli_creation import (  # noqa: E402
    cmd_backlog_add,
    cmd_backlog_list,
    cmd_backlog_migrate,
    cmd_create_task,
    cmd_promote,
)
from _cli_lifecycle import (  # noqa: E402
    cmd_block,
    cmd_cancel,
    cmd_doctor,
    cmd_finish,
    cmd_init,
    cmd_ready,
    cmd_status,
    cmd_unblock,
    cmd_validate,
)
from _cli_meta import cmd_docs_check, cmd_render  # noqa: E402
from _cli_tasks import cmd_tasks_filter, cmd_tasks_list, cmd_tasks_show  # noqa: E402
from _constants import (  # noqa: E402
    KIND_FEATURE,
    KIND_ISSUE,
    ROOT,
    STATUS_AWAITING_VALIDATION,
    STATUS_IN_DEVELOPMENT,
    STATUS_VALIDATED,
)


def _add_task_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("title")
    parser.add_argument("--context", default="")
    parser.add_argument("--origin", default=f"AI process ({today()})")


def _add_promote_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--title")
    parser.add_argument("--context")
    parser.add_argument("--assessment", action="append", default=[])
    parser.add_argument("--plan", action="append", default=[])
    parser.add_argument("--worktree", action="store_true")
    parser.add_argument("--worktree-path")
    parser.add_argument("--branch")
    parser.add_argument(
        "--create-worktree",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--remove-worktree-on-finish",
        action=argparse.BooleanOptionalAction,
        default=True,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Portable AI process commands.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Create .ai process files for this repo.")
    p_init.add_argument("--project-name", default=ROOT.name)
    p_init.add_argument("--force", action="store_true")
    p_init.set_defaults(func=cmd_init)

    p_feature = sub.add_parser("feature", help="Create a feature task.")
    _add_task_args(p_feature)
    p_feature.set_defaults(func=lambda args: cmd_create_task(args, KIND_FEATURE))

    p_issue = sub.add_parser("issue", help="Create an issue task.")
    _add_task_args(p_issue)
    p_issue.set_defaults(func=lambda args: cmd_create_task(args, KIND_ISSUE))

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
    p_finish.add_argument(
        "--commit",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
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

    p_cancel = sub.add_parser(
        "cancel",
        help="Cancel a task with a mandatory reason (status -> Cancelada).",
    )
    p_cancel.add_argument("task_id", nargs="?")
    p_cancel.add_argument(
        "--reason",
        required=True,
        help="Motivo do cancelamento (obrigatorio).",
    )
    p_cancel.add_argument(
        "--keep-worktree",
        action="store_true",
        help="Nao remove worktree associada (default: remove).",
    )
    p_cancel.add_argument(
        "--set-current",
        action="store_true",
        help="Mantem a task como current apos cancelar (default: limpa current).",
    )
    p_cancel.set_defaults(func=cmd_cancel)

    p_block = sub.add_parser(
        "block",
        help="Pause a task with a mandatory reason (status -> Bloqueada).",
    )
    p_block.add_argument("task_id", nargs="?")
    p_block.add_argument(
        "--reason",
        required=True,
        help="Motivo do bloqueio (obrigatorio).",
    )
    p_block.set_defaults(func=cmd_block)

    p_unblock = sub.add_parser(
        "unblock",
        help="Resume a blocked task (status Bloqueada -> Em desenvolvimento).",
    )
    p_unblock.add_argument("task_id", nargs="?")
    p_unblock.add_argument(
        "--note",
        help="Anotacao opcional sobre o desbloqueio.",
    )
    p_unblock.set_defaults(func=cmd_unblock)

    p_validate = sub.add_parser(
        "validate",
        help="Deprecated alias: mark task as validated without committing.",
    )
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
    p_backlog_migrate = backlog_sub.add_parser(
        "migrate",
        help="Move legacy B-NNN de backlog.json para tasks.json (ADR-0011 Fase 2).",
    )
    p_backlog_migrate.add_argument(
        "--dry-run",
        action="store_true",
        help="Lista o que seria migrado sem escrever. Default.",
    )
    p_backlog_migrate.add_argument(
        "--force",
        action="store_true",
        help="Aplica a migracao (move B-NNN para tasks.json e esvazia backlog.json).",
    )
    p_backlog_migrate.set_defaults(func=cmd_backlog_migrate)
    p_backlog_promote = backlog_sub.add_parser("promote", help="Promote backlog item.")
    p_backlog_promote.add_argument("backlog_id")
    p_backlog_promote.add_argument("--kind", choices=[KIND_FEATURE, KIND_ISSUE], default=KIND_FEATURE)
    _add_promote_args(p_backlog_promote)
    p_backlog_promote.set_defaults(func=cmd_promote)

    p_promote = sub.add_parser("promote", help="Promote a backlog item to feature or issue.")
    p_promote.add_argument("backlog_id")
    p_promote.add_argument("--kind", choices=[KIND_FEATURE, KIND_ISSUE], required=True)
    _add_promote_args(p_promote)
    p_promote.set_defaults(func=cmd_promote)

    p_doctor = sub.add_parser("doctor", help="Check process files + manifest + render + lock_api.")
    p_doctor.add_argument("--strict", action="store_true", help="Trata warnings como erros.")
    p_doctor.add_argument("--skip-render", action="store_true", help="Pula `render --check` (uso em CI rapido).")
    p_doctor.set_defaults(func=cmd_doctor)

    p_tasks = sub.add_parser("tasks", help="List, show, or filter tasks (F-017).")
    tasks_sub = p_tasks.add_subparsers(dest="tasks_command", required=True)

    p_tasks_list = tasks_sub.add_parser("list", help="List all tasks (newest first).")
    p_tasks_list.add_argument("--limit", type=int, default=None, help="Limita aos N mais recentes.")
    p_tasks_list.add_argument("--json", action="store_true", help="Saida em JSON.")
    p_tasks_list.set_defaults(func=cmd_tasks_list)

    p_tasks_show = tasks_sub.add_parser("show", help="Show full task by ID.")
    p_tasks_show.add_argument("task_id")
    p_tasks_show.add_argument("--json", action="store_true", help="Saida em JSON (exit 1 se nao encontrar).")
    p_tasks_show.set_defaults(func=cmd_tasks_show)

    p_tasks_filter = tasks_sub.add_parser("filter", help="Filter tasks by status/kind/limit.")
    p_tasks_filter.add_argument(
        "--status",
        choices=[
            STATUS_IN_DEVELOPMENT,
            STATUS_AWAITING_VALIDATION,
            STATUS_VALIDATED,
        ],
        help="Filtra por status exato.",
    )
    p_tasks_filter.add_argument(
        "--kind",
        choices=[KIND_FEATURE, KIND_ISSUE],
        help="Filtra por kind.",
    )
    p_tasks_filter.add_argument("--limit", type=int, default=None, help="Limita aos N mais recentes.")
    p_tasks_filter.add_argument("--json", action="store_true", help="Saida em JSON.")
    p_tasks_filter.set_defaults(func=cmd_tasks_filter)

    p_render = sub.add_parser(
        "render",
        help="Render per-agent skill files from core/manifest/manifest.yaml.",
    )
    p_render.add_argument("--check", action="store_true", help="Exit 1 se algum alvo gerado estiver stale.")
    p_render.add_argument("--verb", help="Renderiza apenas um verbo do manifest.")
    p_render.set_defaults(func=cmd_render)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
