#!/usr/bin/env python3
"""Portable Guia Fluxo CLI for agents and humans.

Entry point only. Each subcommand delegates to a handler under `_cli_*`.
Domain logic lives in `_tasks`, `_features_md`, `_docs_hook`, `_locks`,
`_worktree`, `_commit`. Persistence in `_state`. Git in `_git_ops`.
Constants/messages in `_constants`.

Usage examples:
    python core/src/guia.py feature "Nova tela de revisao"
    python core/src/guia.py bug "Filtro quebra no endpoint"
    python core/src/guia.py backlog add "Ideia futura"
    python core/src/guia.py ready D-016 --file core/src/guia.py
    python core/src/guia.py finish D-016 --lock --lock-id guia-fluxo
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _bootstrap_sys_path() -> None:
    """Ensure sibling modules (_constants, lock_api, ...) are importable.

    When invoked as a script (`python core/src/guia.py ...`), Python sets
    sys.path[0] to the script's directory automatically, so siblings in
    `core/src/` work. We additionally add `core/lock/` to support
    `import lock_api` in dev. In the plugins/guia/ layout everything is flat
    under plugins/guia/bin/ so this is a no-op.
    """
    here = Path(__file__).resolve().parent
    candidates = [here, here.parent / "lock"]
    for candidate in candidates:
        path_str = str(candidate)
        if candidate.exists() and path_str not in sys.path:
            sys.path.insert(0, path_str)


def _bootstrap_utf8_io() -> None:
    """Force stdout/stderr to UTF-8 so demand-title e listas com emoji
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
    STATUS_CLI_CHOICES,
    cmd_backlog_add,
    cmd_backlog_list,
    cmd_backlog_migrate,
    cmd_backlog_resolve,
    cmd_create_epic,
    cmd_create_task,
    cmd_promote,
)
from _cli_lifecycle import (  # noqa: E402
    cmd_block,
    cmd_cancel,
    cmd_doctor,
    cmd_finish,
    cmd_init,
    cmd_plan,
    cmd_upgrade,
    cmd_ready,
    cmd_start,
    cmd_status,
    cmd_unblock,
    cmd_validate,
    ensure_initialized,
)
from _cli_deps import (  # noqa: E402
    cmd_depends_add,
    cmd_depends_list,
    cmd_depends_remove,
)
from _cli_meta import cmd_docs_check, cmd_render  # noqa: E402
from _cli_tasks import (  # noqa: E402
    cmd_stats,
    cmd_tasks_filter,
    cmd_tasks_list,
    cmd_tasks_show,
)
from _constants import (  # noqa: E402
    KIND_BUG,
    KIND_CHORE,
    KIND_FEATURE,
    KIND_ISSUE,
    ROOT,
    STATUS_AWAITING_VALIDATION,
    STATUS_IN_DEVELOPMENT,
    STATUS_VALIDATED,
)


# Kinds aceitos para criacao de NOVAS demandas (Fase 4 do ADR-0011).
# `issue` deixou de ser opcao - tasks legacy com kind=issue continuam
# renderizando (KIND_LABELS tem entrada "Bug (legacy)") mas nenhum verbo
# do CLI cria novas com este kind.
_KIND_CHOICES_NEW = [KIND_FEATURE, KIND_BUG, KIND_CHORE]

# Filtros aceitos por `tasks filter --kind`. Inclui legacy `issue` para
# que o operador consiga listar tasks antigas com aquele kind.
_KIND_CHOICES_FILTER = [KIND_FEATURE, KIND_BUG, KIND_CHORE, KIND_ISSUE]


def _add_task_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("title")
    parser.add_argument("--context", default="")
    parser.add_argument("--origin", default=f"Guia Fluxo ({today()})")
    parser.add_argument(
        "--depends-on",
        action="append",
        default=[],
        metavar="D-XYZ",
        help="Declara dependencia de outra demanda (D-067). Repetivel. "
             "start/promote serao bloqueados ate a dependencia ficar Validada/Finalizada/Resolvida/Cancelada.",
    )
    parser.add_argument(
        "--under",
        metavar="E-NNN",
        help="Cria a task como filho de um Epic existente (D-049). "
             "Hierarquia de 2 niveis so (epic -> story, sem aninhar epics).",
    )
    parser.add_argument(
        "--status",
        choices=STATUS_CLI_CHOICES,
        default="in-development",
        help=(
            "Status inicial da demanda (ADR-0011 Fase 3). "
            "`backlog` = parqueada; `planned` = triada mas nao iniciada; "
            "`in-development` (default) = comeca a implementacao agora."
        ),
    )


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
    parser = argparse.ArgumentParser(description="Portable Guia Fluxo commands.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser(
        "init",
        help="Seed .guia/ state and deploy the per-project lock config + commit-msg hook.",
    )
    p_init.add_argument("--project-name", default=ROOT.name)
    p_init.add_argument("--force", action="store_true")
    p_init.add_argument(
        "--no-locks",
        action="store_true",
        help="Seed .guia/ only; skip the lock registry, commit-msg hook and hooksPath.",
    )
    p_init.set_defaults(func=cmd_init)

    p_upgrade = sub.add_parser(
        "upgrade",
        help="Migra projeto do layout antigo (FEATURES.md + features/) para o atual (.guia/DEMANDAS.md + .guia/locks/).",
    )
    p_upgrade.add_argument(
        "--dry-run",
        action="store_true",
        help="Lista o plano sem mutar. Default executa.",
    )
    p_upgrade.set_defaults(func=cmd_upgrade)

    p_feature = sub.add_parser("feature", help="Create a feature task.")
    _add_task_args(p_feature)
    p_feature.set_defaults(func=lambda args: cmd_create_task(args, KIND_FEATURE))

    p_bug = sub.add_parser(
        "bug",
        help="Create a bug task (substitui o antigo `issue`).",
    )
    _add_task_args(p_bug)
    p_bug.set_defaults(func=lambda args: cmd_create_task(args, KIND_BUG))

    p_chore = sub.add_parser(
        "chore",
        help="Create a chore task (manutencao sem mudanca de comportamento).",
    )
    _add_task_args(p_chore)
    p_chore.set_defaults(func=lambda args: cmd_create_task(args, KIND_CHORE))

    p_epic = sub.add_parser(
        "epic",
        help="Create an Epic (E-NNN) — orquestrador de stories (D-049).",
    )
    p_epic.add_argument("title")
    p_epic.add_argument("--context", default="")
    p_epic.add_argument("--origin", default=f"Guia Fluxo ({today()})")
    p_epic.add_argument(
        "--status",
        choices=STATUS_CLI_CHOICES,
        default="in-development",
        help="Status inicial do Epic. Default: in-development.",
    )
    p_epic.add_argument(
        "--depends-on", action="append", default=[], metavar="D-XYZ",
        help="Declara dependencia (D-067). Repetivel.",
    )
    p_epic.set_defaults(func=cmd_create_epic)

    p_status = sub.add_parser("status", help="Show current task or a given task.")
    p_status.add_argument("task_id", nargs="?")
    p_status.add_argument(
        "--all",
        action="store_true",
        help="Quadro: lista todas as tasks Em desenvolvimento (avisa se houver mais de uma ativa).",
    )
    p_status.set_defaults(func=cmd_status)

    p_ready = sub.add_parser("ready", help="Move task to developer validation stage.")
    p_ready.add_argument("task_id", nargs="?")
    p_ready.add_argument("--file", action="append", default=[])
    p_ready.add_argument("--summary", action="append", default=[])
    p_ready.add_argument("--validation", action="append", default=[])
    p_ready.add_argument("--pending", action="append", default=[])
    p_ready.add_argument("--run-tests", action="store_true")
    p_ready.add_argument(
        "--commit-subject",
        help=(
            "Subject de commit pronto, seguindo a skill de convencao do usuario "
            "(ex.: '✨ feat(D-054): ...'). Persistido na task e usado pelo "
            "finish no lugar do header padrao. Veja a orientacao no corpo de ready.md."
        ),
    )
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
    p_finish.add_argument(
        "--commit-body",
        help="Texto livre anexado ao corpo do commit (complementa summary/validacoes/arquivos).",
    )
    p_finish.add_argument(
        "--commit-subject",
        help=(
            "Subject de commit pronto (skill de convencao do usuario). Substitui "
            "o header padrao; tem precedencia sobre o subject persistido em ready."
        ),
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
    # D-095: gate de qualidade. O agente roda as skills de qualidade sobre
    # modifiedFiles e confirma aqui; sem isso (e sem skip) o finish recusa.
    p_finish.add_argument(
        "--quality-checked",
        action="store_true",
        help="Confirma que a validacao consultiva de qualidade (skills) rodou sobre o que mudou.",
    )
    p_finish.add_argument(
        "--quality-skill",
        action="append",
        default=[],
        help="Skill de qualidade acionada (ex.: clean-code-review). Repetir por skill.",
    )
    p_finish.add_argument(
        "--quality-finding",
        action="append",
        default=[],
        help="Achado/refatoracao aplicada na validacao de qualidade. Repetir por item.",
    )
    p_finish.add_argument(
        "--quality-skip",
        help="Justificativa quando nao ha nada a avaliar na validacao de qualidade.",
    )
    p_finish.set_defaults(func=cmd_finish)

    p_docs_check = sub.add_parser(
        "docs-check",
        help="Lista docs candidatos a atualizacao para a task atual (le .guia/docs-map.yaml).",
    )
    p_docs_check.add_argument("task_id", nargs="?")
    p_docs_check.add_argument(
        "--json",
        action="store_true",
        help="Saida em JSON para consumo por agente.",
    )
    p_docs_check.set_defaults(func=cmd_docs_check)

    p_plan = sub.add_parser(
        "plan",
        help="Mark task as Planejada (triada mas nao iniciada).",
    )
    p_plan.add_argument("task_id", nargs="?")
    p_plan.add_argument(
        "--note",
        help="Anotacao opcional sobre o planejamento.",
    )
    p_plan.set_defaults(func=cmd_plan)

    p_start = sub.add_parser(
        "start",
        help="Iniciar trabalho em uma task Planejada/Backlog (status -> Em desenvolvimento).",
    )
    p_start.add_argument("task_id", nargs="?")
    p_start.add_argument(
        "--note",
        help="Anotacao opcional sobre o inicio do trabalho.",
    )
    p_start.set_defaults(func=cmd_start)

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
    p_backlog_promote.add_argument("--kind", choices=_KIND_CHOICES_NEW, default=KIND_FEATURE)
    _add_promote_args(p_backlog_promote)
    p_backlog_promote.set_defaults(func=cmd_promote)
    p_backlog_resolve = backlog_sub.add_parser(
        "resolve",
        help="Retira do backlog ativo um item ja entregue/obsoleto (status -> Resolvida).",
    )
    p_backlog_resolve.add_argument("backlog_id")
    p_backlog_resolve.add_argument(
        "--reason",
        help="Motivo/origem da resolucao (ex: demanda que entregou o item).",
    )
    p_backlog_resolve.set_defaults(func=cmd_backlog_resolve)

    p_promote = sub.add_parser("promote", help="Promote a backlog item to feature or issue.")
    p_promote.add_argument("backlog_id")
    p_promote.add_argument("--kind", choices=_KIND_CHOICES_NEW, required=True)
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
        choices=_KIND_CHOICES_FILTER,
        help="Filtra por kind (inclui `issue` legacy para tasks antigas).",
    )
    p_tasks_filter.add_argument("--limit", type=int, default=None, help="Limita aos N mais recentes.")
    p_tasks_filter.add_argument("--json", action="store_true", help="Saida em JSON.")
    p_tasks_filter.set_defaults(func=cmd_tasks_filter)

    p_stats = sub.add_parser(
        "stats",
        help="Timing/throughput de uma task: elapsed total, tempo ativo, bloqueios, ciclos (D-052).",
    )
    p_stats.add_argument("task_id", nargs="?")
    p_stats.add_argument("--json", action="store_true", help="Saida em JSON.")
    p_stats.set_defaults(func=cmd_stats)

    p_depends = sub.add_parser(
        "depends",
        help="Gerencia dependencias entre demandas (D-067): add/remove/list.",
    )
    depends_sub = p_depends.add_subparsers(dest="depends_command", required=True)
    p_depends_add = depends_sub.add_parser(
        "add",
        help="Declara dependencia(s) numa task ja existente.",
    )
    p_depends_add.add_argument("task_id", nargs="?")
    p_depends_add.add_argument(
        "--on", action="append", default=[], required=True, metavar="D-XYZ",
        help="ID da dependencia. Repetivel.",
    )
    p_depends_add.set_defaults(func=cmd_depends_add)
    p_depends_remove = depends_sub.add_parser(
        "remove",
        help="Remove dependencia(s) declaradas.",
    )
    p_depends_remove.add_argument("task_id", nargs="?")
    p_depends_remove.add_argument(
        "--on", action="append", default=[], required=True, metavar="D-XYZ",
        help="ID da dependencia a remover. Repetivel.",
    )
    p_depends_remove.set_defaults(func=cmd_depends_remove)
    p_depends_list = depends_sub.add_parser(
        "list",
        help="Lista dependencias da task com status atual.",
    )
    p_depends_list.add_argument("task_id", nargs="?")
    p_depends_list.add_argument("--json", action="store_true", help="Saida em JSON.")
    p_depends_list.set_defaults(func=cmd_depends_list)

    p_render = sub.add_parser(
        "render",
        help="Render per-agent skill files from core/manifest/manifest.yaml.",
    )
    p_render.add_argument("--check", action="store_true", help="Exit 1 se algum alvo gerado estiver stale.")
    p_render.add_argument("--verb", help="Renderiza apenas um verbo do manifest.")
    p_render.set_defaults(func=cmd_render)

    return parser


# Commands that must NOT auto-init the project (D-075). `init` seeds it
# itself; `doctor` reports `.guia/` health and must not mask a missing dir;
# `render` is a dev-only build step over the manifest, unrelated to project
# state.
_NO_AUTO_INIT = frozenset({"init", "doctor", "render", "upgrade"})


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command not in _NO_AUTO_INIT:
        ensure_initialized()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
