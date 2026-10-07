"""CLI handlers: init / status / ready / finish / validate.

Each handler is a thin orchestration over the domain/infrastructure
modules: they parse argparse Namespace and call into _tasks, _docs_hook,
_commit, _locks, etc.
"""

from __future__ import annotations

import argparse
import copy
import os
import sys
from pathlib import Path
from typing import Any

from _clock import now_iso, today
from _commit import commit_task
from _constants import (
    DELIVERY_MODE,
    DELIVERY_MODE_PR,
    GUIA_DIR,
    REGISTRY_FILE,
    DEMAND_TITLE_FILE,
    DOCS_MAP_FILE,
    FEATURES_REL,
    MSG_DEFAULT_FINISH_SUMMARY,
    MSG_DEFAULT_READY_SUMMARY,
    MSG_DEFAULT_VALIDATE_SUMMARY,
    MSG_DEFAULT_VALIDATION_PENDING,
    MSG_NONE_PLACEHOLDER,
    MSG_PROCESS_FILES_OK,
    MSG_TASK_NOT_FOUND,
    MSG_VALIDATE_DEPRECATED,
    BACKLOG_FILE,
    CURRENT_FILE,
    PROCESS_FILE,
    ROOT,
    STATUS_AWAITING_VALIDATION,
    STATUS_AWAITING_VALIDATION_ACCENTED,
    STATUS_BACKLOG,
    STATUS_BLOCKED,
    STATUS_CANCELLED,
    STATUS_FINISHED,
    KIND_EPIC,
    STATUS_IN_DEVELOPMENT,
    STATUSES_SATISFY_DEPENDENCY,
    STATUS_PLANNED,
    STATUS_VALIDATED,
    TASKS_FILE,
    TASKS_SCHEMA_VERSION,
)
from _docs_hook import (
    build_docs_review_record,
    ensure_docs_review_ok,
    load_docs_map,
)
from _features_md import upsert_features_entry
from _locks import lock_task_files
from _paths import relative
from _process_config import default_process
from _quality_hook import (
    build_quality_review_record,
    ensure_quality_review_ok,
)
from _reports import write_report
from _state import copy_if_missing, read_json, write_if_missing, write_json
from _tasks import (
    branch_task_id,
    epic_open_children,
    find_children,
    find_task,
    find_task_or_current,
    format_task_line,
    kind_marker,
    list_tasks,
    merge_list,
    print_demand_title,
    recent_task_ids,
    save_task,
    set_current_task,
    unmet_dependencies,
)


def _ensure_dependencies_met(task: dict[str, Any], verb: str) -> None:
    """D-067: bloqueia start/promote enquanto houver dep aberta.

    Lanca SystemExit com mensagem amigavel listando cada dep aberta e seu
    status atual (ou 'missing' quando o id nao existe).
    """
    unmet = unmet_dependencies(task)
    if not unmet:
        return
    lines = [f"Task {task['id']} tem dependencia(s) abertas - {verb} recusado:"]
    for dep in unmet:
        status = dep["status"] or "missing"
        lines.append(f"  - {dep['id']} [{status}]")
    lines.append(
        "Conclua (ou cancele) as dependencias e tente novamente. "
        "Para inspecionar: `guia depends list " + task["id"] + "`."
    )
    raise SystemExit("\n".join(lines))
from _validation_runner import run_validation_commands
from _worktree import cleanup_task_worktree


def initialize_project(project_name: str, force: bool = False) -> None:
    """Create `.guia/` scaffolding (process.json + empty state) at ROOT.

    Idempotent: existing files are preserved unless `force=True`. Shared by
    the explicit `init` command and by the auto-init path (D-075) so a
    consumer project that installed the plugin without a clone works on the
    first command, no manual `init` required.
    """
    GUIA_DIR.mkdir(parents=True, exist_ok=True)
    write_if_missing(PROCESS_FILE, default_process(project_name), force=force)
    write_if_missing(TASKS_FILE, {"schemaVersion": TASKS_SCHEMA_VERSION, "tasks": []}, force=force)
    write_if_missing(BACKLOG_FILE, {"schemaVersion": 1, "items": []}, force=force)
    write_if_missing(CURRENT_FILE, {}, force=force)
    if force or not DEMAND_TITLE_FILE.exists():
        DEMAND_TITLE_FILE.write_text("", encoding="utf-8")


def ensure_initialized() -> None:
    """Auto-init the project on first command if `.guia/` is absent (D-075).

    Runs before state-touching commands so a virgin consumer project works
    without an explicit `init`. Uses the project directory name as the
    default project name. Emits a one-line note to stderr for transparency;
    stays silent once `.guia/process.json` exists.
    """
    if PROCESS_FILE.exists():
        return
    initialize_project(ROOT.name)
    print(
        f"Guia Fluxo: .guia/ ausente em {relative(GUIA_DIR)} - projeto inicializado "
        f"automaticamente ({ROOT.name}).",
        file=sys.stderr,
    )


# Per-project templates deployed by the explicit `init` (D-076). Source
# paths are relative to the plugin templates dir; dest paths relative to
# ROOT. Lock data + commit-msg hook turn a virgin project into a fully
# process-guarded one. Auto-init (D-075) seeds `.guia/` only; the lock
# setup is opt-in via `init` (skip with `init --no-locks`).
_LOCK_TEMPLATES: list[tuple[str, str]] = [
    ("locks/registry.yaml", ".guia/locks/registry.yaml"),
    ("locks/lock-ignore.txt", ".guia/locks/lock-ignore.txt"),
    (".githooks/commit-msg", ".githooks/commit-msg"),
]


def _plugin_templates_dir() -> Path | None:
    """Locate the bundled `templates/` dir shipped with the engine.

    Prefers `${CLAUDE_PLUGIN_ROOT}/templates` (the installed plugin, set by
    Claude Code when a skill runs); falls back to `<engine>/../templates`,
    which resolves to the shipped `plugins/guia/templates` (dogfood) or
    `core/templates` (source clone). Returns None when no candidate exists
    (e.g. a source clone where the commit-msg hook lives under core/hooks
    and was never promoted) - the caller degrades to seeding `.guia/` only.
    """
    candidates: list[Path] = []
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if plugin_root:
        candidates.append(Path(plugin_root) / "templates")
    candidates.append(Path(__file__).resolve().parent.parent / "templates")
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


def deploy_lock_templates(force: bool = False) -> tuple[list[str], list[str]]:
    """Copy the per-project lock config + commit-msg hook into ROOT.

    Idempotent and non-clobbering by default: existing files are preserved
    (returned in `skipped`) unless `force=True`. Returns
    `(written, skipped)` as ROOT-relative path strings. Templates absent
    from the bundle are quietly ignored (degrades on partial source clones).
    """
    templates_dir = _plugin_templates_dir()
    written: list[str] = []
    skipped: list[str] = []
    if templates_dir is None:
        return written, skipped
    for src_rel, dst_rel in _LOCK_TEMPLATES:
        src = templates_dir / src_rel
        if not src.exists():
            continue
        dst = ROOT / dst_rel
        if copy_if_missing(src, dst, force=force):
            # Git ignores non-executable hooks on POSIX; mark it +x. The
            # chmod is a harmless no-op on Windows.
            if dst_rel.startswith(".githooks/"):
                try:
                    dst.chmod(0o755)
                except OSError:
                    pass
            written.append(dst_rel)
        else:
            skipped.append(dst_rel)
    return written, skipped


def configure_hooks_path() -> str | None:
    """Point git at `.githooks/` unless the repo already set core.hooksPath.

    Returns the value now in effect (".githooks" if we set it, or the
    pre-existing value we left untouched), or None when git is unavailable
    or ROOT is not a git repo. Never clobbers an existing hooksPath - a
    consumer that already routes hooks elsewhere keeps its choice.
    """
    if not (ROOT / ".git").exists():
        return None
    from _git_ops import has_git

    if not has_git():
        return None
    import subprocess

    existing = subprocess.run(
        ["git", "config", "--local", "core.hooksPath"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if existing.returncode == 0 and existing.stdout.strip():
        return existing.stdout.strip()
    result = subprocess.run(
        ["git", "config", "--local", "core.hooksPath", ".githooks"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return ".githooks"


def cmd_init(args: argparse.Namespace) -> int:
    initialize_project(args.project_name, force=args.force)
    print(f"Guia Fluxo initialized for {args.project_name}.")
    if getattr(args, "no_locks", False):
        return 0
    written, skipped = deploy_lock_templates(force=args.force)
    for rel in written:
        print(f"  + {rel}")
    for rel in skipped:
        print(f"  = {rel} (preservado)")
    hook_present = any(
        rel.startswith(".githooks/") for rel in (*written, *skipped)
    )
    if hook_present:
        configured = configure_hooks_path()
        if configured == ".githooks":
            print("  + git core.hooksPath -> .githooks")
        elif configured:
            print(f"  = git core.hooksPath ja definido ({configured}) - preservado")
    if written:
        print(
            "Locks ativos: arquivos travados em .guia/locks/registry.yaml exigem "
            "[unlock:<id>] motivo: <razao> na mensagem de commit."
        )
    return 0


# D-091: migracoes do layout antigo (raiz) para o atual (.guia/). Cada
# entrada e (origem-relativa-ROOT, destino-relativa-ROOT). Ordem importa:
# o catalogo primeiro, depois os locks - mantem o output legivel.
_UPGRADE_MOVES: list[tuple[str, str]] = [
    ("FEATURES.md", ".guia/DEMANDAS.md"),
    ("features/registry.yaml", ".guia/locks/registry.yaml"),
    ("features/lock-ignore.txt", ".guia/locks/lock-ignore.txt"),
]


def cmd_upgrade(args: argparse.Namespace) -> int:
    """D-091: migra o projeto do layout antigo (FEATURES.md + features/) para
    o layout atual (.guia/DEMANDAS.md + .guia/locks/). Idempotente:
    nada para mover = NOOP. Move com `git mv` quando o repo e git e o
    arquivo esta rastreado (preserva historico); cai para `shutil.move`
    quando nao da. `--dry-run` lista o plano sem mutar.
    """
    import shutil
    import subprocess

    plan: list[tuple[Path, Path]] = []
    blockers: list[str] = []
    for src_rel, dst_rel in _UPGRADE_MOVES:
        src = ROOT / src_rel
        dst = ROOT / dst_rel
        if not src.exists():
            continue
        if dst.exists():
            blockers.append(f"  ! {src_rel} -> {dst_rel} (destino ja existe; resolva a mao)")
            continue
        plan.append((src, dst))

    if blockers:
        for line in blockers:
            print(line, file=sys.stderr)
        return 1

    if not plan:
        print("Layout ja esta atualizado. Nada a migrar.")
        return 0

    print("Plano de migracao:")
    for src, dst in plan:
        print(f"  + {src.relative_to(ROOT).as_posix()} -> {dst.relative_to(ROOT).as_posix()}")

    if args.dry_run:
        print("\n--dry-run: nada foi mutado. Re-rode sem --dry-run para aplicar.")
        return 0

    git_dir = (ROOT / ".git").is_dir()
    for src, dst in plan:
        dst.parent.mkdir(parents=True, exist_ok=True)
        moved_by_git = False
        if git_dir:
            try:
                subprocess.run(
                    ["git", "-C", str(ROOT), "mv", str(src.relative_to(ROOT)), str(dst.relative_to(ROOT))],
                    check=True, capture_output=True, text=True,
                )
                moved_by_git = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass  # arquivo nao rastreado ou git ausente -> fallback
        if not moved_by_git:
            shutil.move(str(src), str(dst))
        print(f"  moved {src.relative_to(ROOT).as_posix()} -> {dst.relative_to(ROOT).as_posix()}")

    # Remove features/ se ficou vazio (clean-up cosmetico).
    features_dir = ROOT / "features"
    if features_dir.is_dir() and not any(features_dir.iterdir()):
        features_dir.rmdir()
        print("  rmdir features/ (vazio)")

    print(f"\nMigracao concluida: {len(plan)} arquivo(s) movido(s).")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    import json

    if getattr(args, "all", False):
        return _status_board()

    task = find_task_or_current(args.task_id)
    # D-049: Epic ganha visualizacao agregada (arvore + progresso). JSON
    # cru desaparece para epics, que sao orquestradores; quem quiser o
    # JSON usa `tasks show <id>`.
    if task.get("kind") == KIND_EPIC:
        _print_epic_tree(task)
        print_demand_title(task)
        return 0
    print(json.dumps(task, ensure_ascii=False, indent=2))
    print_demand_title(task)
    return 0


def _print_epic_tree(epic: dict[str, Any]) -> None:
    """D-049: imprime arvore do Epic com progresso filhos terminados/total."""
    children = find_children(epic["id"])
    open_count = sum(
        1 for c in children if c.get("status") not in STATUSES_SATISFY_DEPENDENCY
    )
    closed_count = len(children) - open_count

    epic_line = format_task_line(epic)
    print(epic_line)
    print(f"  Progresso: {closed_count}/{len(children)} filhos terminados")
    if not children:
        print("  (sem filhos ainda - adicione com `feature/bug/chore --under " + epic["id"] + "`)")
        return
    for index, child in enumerate(children):
        prefix = "    └─" if index == len(children) - 1 else "    ├─"
        marker = kind_marker(child.get("kind", ""))
        print(
            f"{prefix} {child['id']} {marker} [{child.get('status', '?')}] "
            f"{child.get('title', '')}"
        )
    if open_count:
        print(
            f"\nBloqueio: finish {epic['id']} falhara enquanto "
            f"{open_count} filho(s) nao estiverem em status terminal "
            "(Validada/Finalizada/Resolvida/Cancelada)."
        )


def _status_board() -> int:
    """Visao de quadro (B-014): lista todas as tasks `Em desenvolvimento`.

    Quando ha mais de uma task ativa ao mesmo tempo, avisa sobre a
    ambiguidade do `current-task.json` global (B-018): comandos sem id
    explicito caem em find_task_or_current(None) e podem pegar a task
    errada. O aviso e informativo - o fix estrutural fica para B-018.
    """
    active = list_tasks(status=STATUS_IN_DEVELOPMENT)
    if not active:
        print("Nenhuma task em desenvolvimento.")
        return 0
    current_id = read_json(CURRENT_FILE, {}).get("taskId")
    for task in active:
        line = format_task_line(task)
        if task.get("id") == current_id:
            line += "  <- current"
        print(line)
    if len(active) > 1:
        print(
            f"\nAviso: {len(active)} tasks em desenvolvimento ao mesmo tempo. "
            "Comandos sem id explicito usam o current-task.json global e podem "
            "pegar a task errada (B-018) - passe o id (ex: `ready D-079`)."
        )
    return 0


def _is_bookkeeping(path: str) -> bool:
    """D-105: True para arquivos de processo do Guia (`.guia/...`) - catalogo,
    locks, estado. Toda demanda os co-commita; nao contam como 'trabalho de
    produto' na hora de decidir se algo precisa ser declarado via --file."""
    return path.replace("\\", "/").startswith(".guia/")


def _declared_product_files(task: dict[str, Any]) -> list[str]:
    """D-105: arquivos de PRODUTO ja declarados na task (via --file de um
    ready/finish anterior), excluindo bookkeeping e o placeholder."""
    return [
        value
        for value in task.get("modifiedFiles", [])
        if value and value != MSG_NONE_PLACEHOLDER and not _is_bookkeeping(value)
    ]


def cmd_ready(args: argparse.Namespace) -> int:
    task = find_task_or_current(args.task_id)
    config = read_json(PROCESS_FILE, default_process(ROOT.name))
    # D-105: os arquivos da demanda vem SO do que foi declarado (--file), nunca
    # da arvore inteira. `git diff HEAD` incluiria o trabalho de outras demandas
    # em paralelo, contaminando modifiedFiles (que o finish depois commita).
    changed_files = list(args.file)
    task["status"] = config.get("ready", {}).get("status", STATUS_AWAITING_VALIDATION)
    # D-052: marca a entrega para validacao. readyAt guarda o ultimo ready;
    # readyCount conta os ciclos ready->finish (cada re-ready incrementa).
    task["readyAt"] = now_iso()
    task["readyCount"] = task.get("readyCount", 0) + 1
    merge_list(task, "modifiedFiles", changed_files)
    merge_list(task, "summary", args.summary or [MSG_DEFAULT_READY_SUMMARY])
    merge_list(task, "validations", args.validation)
    task["pending"] = args.pending or [MSG_DEFAULT_VALIDATION_PENDING]

    # D-054: subject de commit pronto pela skill de convencao do usuario.
    # Persistido na task para o finish (humano) usar sem o agente reconstruir.
    commit_subject = getattr(args, "commit_subject", None)
    if commit_subject and commit_subject.strip():
        task["commitSubject"] = commit_subject.strip()

    if args.run_tests or config.get("ready", {}).get("runValidationByDefault", False):
        run_validation_commands(task, config, "ready")

    save_task(task)
    set_current_task(task)
    upsert_features_entry(task)
    write_report(task, "ready")

    print(f"{task['id']} moved to {task['status']}.")
    print_demand_title(task)
    return 0


# D-103: estados a partir dos quais `finish` faz sentido. Fechar e terminal
# (Validada) e irreversivel; so aceitamos demandas ja entregues para validacao
# ou ainda em desenvolvimento (atalho ready->finish num passo). Backlog/Planejada
# precisam de start/ready antes; estados terminais ja foram fechados.
_FINISHABLE_STATUSES = frozenset(
    {
        STATUS_AWAITING_VALIDATION,
        STATUS_AWAITING_VALIDATION_ACCENTED,
        STATUS_IN_DEVELOPMENT,
    }
)


def _resolve_terminal_target(
    task_id: str | None,
    *,
    verb: str,
    example_id: str,
    candidates: list[dict[str, Any]],
    candidates_label: str,
    empty_hint: str,
    from_branch: bool = False,
) -> dict[str, Any]:
    """D-103/D-104: resolve a demanda de um verbo TERMINAL sem cair no ponteiro.

    Verbos terminais (`finish`, `cancel`) sao irreversiveis: `finish` commita e
    marca Validada, `cancel` marca Cancelada. Ate o D-103 ambos confiavam no
    ponteiro `current-task.json` quando nenhum id era passado. Esse ponteiro e
    unico por copia de trabalho: outra sessao/chat na mesma pasta o sobrescreve,
    e um verbo terminal sem id podia agir sobre uma demanda que este chat nunca
    tocou (o incidente do D-103: o ponteiro driftou para uma D-NNN em Backlog de
    outro chat e o `finish` a finalizou).

    O motor nao tem conceito de "chat" (Op B do D-096 foi descartada por isso),
    entao quem sabe qual demanda este chat conduz e o agente - que deve passar o
    id explicito. Aqui, portanto, NAO deduzimos do ponteiro: com id, usamos ele;
    sem id, recusamos e listamos as candidatas (parametrizadas por verbo) para
    ajudar o operador a escolher a certa.

    D-110: com `from_branch`, a branch de demanda do modo `pr` conta como id
    explicito - ela e do worktree desta sessao, nao um ponteiro compartilhado.
    """
    if not task_id and from_branch:
        task_id = branch_task_id()
    if task_id:
        task = find_task(task_id)
        if task is None:
            suggestions = recent_task_ids()
            hint = f" Recentes: {', '.join(suggestions)}" if suggestions else ""
            raise SystemExit(MSG_TASK_NOT_FOUND.format(id=task_id) + hint)
        return task

    lines = [
        f"{verb} exige o id explicito da demanda ativa deste chat "
        f"(ex: `{verb} {example_id}`).",
        "Esta acao e terminal e irreversivel: o motor nao deduz do "
        "current-task.json global, que pode ter driftado de outra sessao para "
        "uma demanda que este chat nunca tocou (D-103/D-104).",
    ]
    if candidates:
        lines.append(candidates_label)
        for candidate in candidates:
            lines.append(f"  - {candidate['id']} {candidate.get('title', '')}")
    else:
        lines.append(empty_hint)
    raise SystemExit("\n".join(lines))


def _resolve_finish_target(task_id: str | None) -> dict[str, Any]:
    """D-103: resolve a demanda a finalizar SEM cair no current-task.json global.

    Fino wrapper sobre `_resolve_terminal_target`: sem id, lista as candidatas em
    Aguardando validacao (o estado esperado de quem chega no finish).
    """
    return _resolve_terminal_target(
        task_id,
        verb="finish",
        example_id="D-173",
        candidates=list_tasks(status=STATUS_AWAITING_VALIDATION),
        candidates_label="Candidatas em Aguardando validacao:",
        from_branch=True,
        empty_hint=(
            "Nenhuma task em Aguardando validacao agora - rode `ready <id>` "
            "antes, ou passe o id da demanda deste chat."
        ),
    )


def cmd_finish(args: argparse.Namespace) -> int:
    # D-098: `finish` e acao do usuario, garantida por REGRA DE COMPORTAMENTO
    # (skill/AGENTS/CLAUDE), nao por gate tecnico no motor. O gate por env
    # GUIA_HUMAN_FINISH (D-080) foi removido: mandar variavel era ruim e o
    # motor nao consegue distinguir agente de humano sem um sinal artificial.
    # O agente nunca dispara finish por conta propria - so quando o usuario
    # solicita `/guia:finish` ou autoriza explicitamente.
    #
    # D-103: resolucao NAO usa o current-task.json global (footgun de drift
    # entre chats). Exige id explicito; sem id, recusa e lista candidatas.
    task = _resolve_finish_target(args.task_id)
    # D-103: guard de status - so finaliza de um estado finalizavel. Barra o
    # incidente na raiz: finalizar por engano uma demanda em Backlog/Planejada
    # (ou re-finalizar uma ja terminal) agora e recusado antes de qualquer
    # mutacao, com o status atual no erro.
    current_status = task.get("status")
    if current_status not in _FINISHABLE_STATUSES:
        raise SystemExit(
            f"Task {task['id']} esta em '{current_status}' - finish so aceita "
            f"demanda em [{', '.join(sorted(_FINISHABLE_STATUSES))}]. "
            "Backlog/Planejada precisam de `start`/`ready` antes; estados "
            "terminais (Validada/Finalizada/Cancelada) ja foram fechados."
        )
    # D-049: Epic so fecha quando todos os filhos forem terminais.
    if task.get("kind") == KIND_EPIC:
        open_kids = epic_open_children(task["id"])
        if open_kids:
            lines = [
                f"Epic {task['id']} tem {len(open_kids)} filho(s) abertos - finish recusado:"
            ]
            for kid in open_kids:
                lines.append(
                    f"  - {kid['id']} [{kid.get('status', '?')}] {kid.get('title', '')}"
                )
            lines.append(
                "Conclua (ou cancele) cada filho e tente novamente. "
                f"Para ver a arvore: `guia status {task['id']}`."
            )
            raise SystemExit("\n".join(lines))
    config = read_json(PROCESS_FILE, default_process(ROOT.name))
    # D-105: os arquivos da demanda vem SO do que foi declarado (--file), nunca
    # da arvore inteira - `git diff HEAD` inclui o trabalho de outras demandas
    # em paralelo e o commit as engoliria.
    changed_files = list(args.file)

    # D-105: no caminho de commit exigimos os arquivos de produto declarados.
    # Sem isso, um finish sem --file commitaria so o bookkeeping (.guia/) e
    # deixaria o codigo real de fora - ou, no modelo antigo (git add -A da
    # arvore), engoliria arquivos de outras demandas. Epicos sao orquestradores
    # (fecham commitando so o catalogo), entao ficam de fora do gate.
    commit_requested = args.commit
    if DELIVERY_MODE == DELIVERY_MODE_PR:
        # D-111: no modo `pr` o codigo chega a main pelo squash do PR; o
        # finish so fecha o estado. Commit aqui cairia na arvore principal
        # (ROOT), mesmo rodado de um worktree - por isso nem `commitByDefault`
        # nem `--commit` valem.
        if commit_requested:
            raise SystemExit(
                f"finish {task['id']}: no modo `pr` (delivery.mode) o codigo entra "
                "pela main via squash do PR; o finish nao commita. Rode sem --commit."
            )
        commit_requested = False
    elif commit_requested is None:
        commit_requested = config.get("finish", {}).get("commitByDefault", True)
    if (
        commit_requested
        and task.get("kind") != KIND_EPIC
        and not changed_files
        and not _declared_product_files(task)
    ):
        raise SystemExit(
            f"finish {task['id']} vai commitar, mas nenhum arquivo de produto "
            "desta demanda foi declarado.\n"
            "O motor NAO infere da arvore inteira (D-105): `git diff HEAD` "
            "inclui o trabalho de outras demandas rodando em paralelo, e o "
            "commit as engoliria.\n"
            "Declare os arquivos que ESTA demanda tocou:\n"
            f"  finish {task['id']} --file <path> [--file <path> ...]\n"
            "Ou feche sem commitar agora com --no-commit."
        )

    docs_map = load_docs_map()
    if docs_map is not None:
        ensure_docs_review_ok(task, changed_files, docs_map, args)
    else:
        print(
            "docs-check: .guia/docs-map.yaml nao encontrado. "
            "Pulando hook de docs. "
            "Crie o mapa para ativar o controle de docs (docs/reference/docs-map.md).",
            file=sys.stderr,
        )

    # D-095: validacao consultiva de qualidade (skills) antes de fechar. O core
    # apenas sinaliza+exige; a skill `guia:finish` roda as skills de qualidade
    # sobre modifiedFiles. Barra aqui (antes de qualquer mutacao de status) para
    # nao deixar a task meio-fechada, espelhando o docs-gate e o gate humano.
    ensure_quality_review_ok(task, changed_files, config, args)

    finish_config = config.get("finish", {})
    # D-081/D-111: foto da demanda e das travas antes de qualquer mutacao. Se
    # o commit falhar, tudo volta - nao so o status (D-081 revertia status e
    # finishedAt, mas deixava gravados o registro do portao, resumo, arquivos
    # e a trava nova: o "grava o gate, nao muda o status" da D-579).
    task_before = copy.deepcopy(task)
    registry_before = REGISTRY_FILE.read_bytes() if REGISTRY_FILE.exists() else None
    task["status"] = finish_config.get("status", STATUS_VALIDATED)
    task["finishedAt"] = now_iso()
    merge_list(task, "modifiedFiles", changed_files)
    merge_list(task, "modifiedFiles", args.docs_touched)
    merge_list(task, "summary", args.summary or [MSG_DEFAULT_FINISH_SUMMARY])
    merge_list(task, "validations", args.validation)
    task["pending"] = args.pending or []
    if docs_map is not None:
        task["docsReview"] = build_docs_review_record(
            task, changed_files, docs_map, args
        )
    # D-095: registra a validacao de qualidade (skills rodadas, achados,
    # ou skip) na task para rastreabilidade no report/commit.
    task["qualityReview"] = build_quality_review_record(task, changed_files, args)

    if args.run_tests or finish_config.get("runValidationByDefault", False):
        run_validation_commands(task, config, "finish")

    if args.lock or finish_config.get("lockOnFinish", False):
        lock_task_files(task, args.lock_id, args.lock_description)
        merge_list(task, "modifiedFiles", [".guia/locks/registry.yaml"])
        merge_list(task, "summary", [f"Lock `{args.lock_id}` registrado para os arquivos finalizados."])

    # commit_requested ja foi resolvido acima (D-105 gate), antes das mutacoes.

    save_task(task)
    set_current_task(task)
    upsert_features_entry(task)
    write_report(task, "finish")

    if commit_requested:
        # D-081: atomicidade status<->commit. O status `Validada` so deve
        # persistir se o commit suceder. Se `commit_task` estourar (pathspec,
        # hook de lock, staged inesperado), revertemos a transicao ja gravada
        # para nao deixar a task como Validada sem nenhum commit por tras.
        try:
            # D-054: subject da convencao do usuario — --commit-subject do finish
            # tem precedencia sobre o que foi persistido no ready (commitSubject).
            subject_override = getattr(args, "commit_subject", None) or task.get("commitSubject")
            commit_task(
                task,
                getattr(args, "commit_body", None),
                subject_override,
                getattr(args, "unlock_reason", None),
            )
        except BaseException:
            task.clear()
            task.update(task_before)
            if registry_before is None:
                REGISTRY_FILE.unlink(missing_ok=True)
            else:
                REGISTRY_FILE.write_bytes(registry_before)
            save_task(task)
            set_current_task(task)
            upsert_features_entry(task)
            raise
    cleanup_task_worktree(task, commit_requested)

    print(f"{task['id']} finished as {task['status']}.")
    print_demand_title(task)
    return 0


_TERMINAL_STATUSES = frozenset({STATUS_VALIDATED, STATUS_FINISHED, STATUS_CANCELLED})


def _clear_current_if_matches(task_id: str) -> None:
    current = read_json(CURRENT_FILE, {})
    if current.get("taskId") == task_id:
        write_json(CURRENT_FILE, {})
        DEMAND_TITLE_FILE.write_text("", encoding="utf-8")


def _resolve_cancel_target(task_id: str | None) -> dict[str, Any]:
    """D-104: resolve a demanda a cancelar SEM cair no current-task.json global.

    Mesmo footgun do D-103 no finish: `cancel` e terminal (Cancelada) e
    irreversivel; deduzir do ponteiro global podia cancelar a demanda errada
    quando o ponteiro driftou de outra sessao. Exige id explicito. Sem id, lista
    as candidatas abertas (nao-terminais) - o universo cancelavel e mais amplo
    que o do finish (Backlog/Planejada/Em desenvolvimento/Aguardando/Bloqueada).
    """
    open_candidates = [
        task for task in list_tasks() if task.get("status") not in _TERMINAL_STATUSES
    ]
    return _resolve_terminal_target(
        task_id,
        verb="cancel",
        example_id="D-173",
        candidates=open_candidates,
        candidates_label="Candidatas abertas (nao-terminais):",
        empty_hint=(
            "Nenhuma task aberta agora - nada a cancelar, ou passe o id da "
            "demanda deste chat."
        ),
    )


def cmd_cancel(args: argparse.Namespace) -> int:
    # D-104: resolucao NAO usa o current-task.json global (footgun de drift entre
    # chats, herdado do D-103 no finish). Exige id explicito; sem id, recusa e
    # lista as candidatas abertas.
    task = _resolve_cancel_target(args.task_id)
    if task["status"] in _TERMINAL_STATUSES:
        raise SystemExit(
            f"Task {task['id']} ja esta em estado terminal ({task['status']}); nao pode ser cancelada."
        )

    task["status"] = STATUS_CANCELLED
    task["finishedAt"] = now_iso()  # D-052: Cancelada e estado terminal.
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
    print_demand_title(task)
    return 0


_PLAN_VALID_FROM = frozenset({STATUS_BACKLOG, STATUS_IN_DEVELOPMENT})
_START_VALID_FROM = frozenset({STATUS_BACKLOG, STATUS_PLANNED})


def _attach_features_md(task: dict[str, Any]) -> None:
    """Inclui o catalogo (.guia/DEMANDAS.md) em modifiedFiles quando a task
    sai do backlog e passa a aparecer no catalogo (idempotente)."""
    files = list(task.get("modifiedFiles", []))
    if FEATURES_REL not in files:
        files.append(FEATURES_REL)
    task["modifiedFiles"] = files


def cmd_plan(args: argparse.Namespace) -> int:
    """Move task para `Planejada` (B-017). Aceita Backlog ou
    Em desenvolvimento como ponto de partida. Rejeita estados terminais
    e Aguardando validacao (use cancel/finish em vez disso)."""
    task = find_task_or_current(args.task_id)
    if task["status"] == STATUS_PLANNED:
        raise SystemExit(f"Task {task['id']} ja esta Planejada.")
    if task["status"] not in _PLAN_VALID_FROM:
        valid = ", ".join(sorted(_PLAN_VALID_FROM))
        raise SystemExit(
            f"Task {task['id']} esta em '{task['status']}' - "
            f"plan so aceita transicao de [{valid}]."
        )

    coming_from_backlog = task["status"] == STATUS_BACKLOG
    task["status"] = STATUS_PLANNED
    note = f"Planejada em {today()}"
    if args.note:
        note = f"{note}: {args.note}"
    note += "."
    merge_list(task, "summary", [note])
    if coming_from_backlog:
        _attach_features_md(task)

    save_task(task)
    set_current_task(task)
    upsert_features_entry(task)
    write_report(task, "plan")

    print(f"{task['id']} planned.")
    print_demand_title(task)
    return 0


def cmd_start(args: argparse.Namespace) -> int:
    """Move task para `Em desenvolvimento`. Aceita Backlog (atalho que
    pula Planejada) ou Planejada. Diferente de `promote`: aqui nao
    avalia kind nem ajusta backlogId - assume que a triagem ja foi feita.
    Use `promote` quando ainda precisa decidir feature/bug/chore."""
    task = find_task_or_current(args.task_id)
    if task["status"] == STATUS_IN_DEVELOPMENT:
        raise SystemExit(f"Task {task['id']} ja esta Em desenvolvimento.")
    if task["status"] not in _START_VALID_FROM:
        valid = ", ".join(sorted(_START_VALID_FROM))
        raise SystemExit(
            f"Task {task['id']} esta em '{task['status']}' - "
            f"start so aceita transicao de [{valid}]."
        )
    _ensure_dependencies_met(task, "start")

    coming_from_backlog = task["status"] == STATUS_BACKLOG
    task["status"] = STATUS_IN_DEVELOPMENT
    # D-052: carimba startedAt na primeira entrada em desenvolvimento. Usa
    # set-if-absent para nao sobrescrever se a task ja passou por aqui (o
    # caminho de resumo pos-bloqueio e unblock, que nao reseta o inicio).
    if not task.get("startedAt"):
        task["startedAt"] = now_iso()
    note = f"Em desenvolvimento desde {today()}"
    if args.note:
        note = f"{note}: {args.note}"
    note += "."
    merge_list(task, "summary", [note])
    if coming_from_backlog:
        _attach_features_md(task)

    save_task(task)
    set_current_task(task)
    upsert_features_entry(task)
    write_report(task, "start")

    print(f"{task['id']} started.")
    print_demand_title(task)
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
    # D-052: `at` (so-data) mantido para compat; blockedAt e o carimbo preciso
    # que alimenta o calculo de elapsedBlocked junto com unblockedAt.
    block_record = {"reason": args.reason, "at": today(), "blockedAt": now_iso()}
    task.setdefault("blocks", []).append(block_record)
    merge_list(task, "summary", [f"Bloqueada em {today()}: {args.reason}"])

    save_task(task)
    set_current_task(task)
    upsert_features_entry(task)
    write_report(task, "block")

    print(f"{task['id']} blocked: {args.reason}")
    print_demand_title(task)
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
        # D-052: carimbo preciso para fechar o intervalo de bloqueio.
        blocks[-1]["unblockedAt"] = now_iso()
    note = f"Desbloqueada em {today()}."
    if args.note:
        note = f"Desbloqueada em {today()}: {args.note}"
    merge_list(task, "summary", [note])

    save_task(task)
    set_current_task(task)
    upsert_features_entry(task)
    write_report(task, "unblock")

    print(f"{task['id']} unblocked.")
    print_demand_title(task)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    print(MSG_VALIDATE_DEPRECATED, file=sys.stderr)
    task = find_task_or_current(args.task_id)
    config = read_json(PROCESS_FILE, default_process(ROOT.name))
    task["status"] = config.get("validate", {}).get("status", STATUS_VALIDATED)
    task["finishedAt"] = now_iso()  # D-052: Validada e estado terminal.
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
    print_demand_title(task)
    return 0


def _code_root() -> Path:
    """Arvore cujo codigo o doctor confere (manifest, render, lock_api).

    D-109: no modo `pr`, ROOT e a arvore principal mesmo quando o motor roda
    de um worktree (o estado mora la). O codigo a conferir, porem, e o da
    arvore onde o motor esta - senao o doctor de um worktree aprovaria o
    render da principal. Fora do repo-mae, cai em ROOT, como antes.
    """
    script_tree = Path(__file__).resolve().parents[2]
    return script_tree if (script_tree / "core" / "manifest").is_dir() else ROOT


def _is_dev_repo() -> bool:
    """True when running from the repo-mae (has core/manifest/).

    In the consumer (.guia-fluxo/bin/ flat layout), core/ does not exist;
    the extended checks degrade to "lite" mode (just .guia/ files + git).
    """
    return (_code_root() / "core" / "manifest").is_dir()


def cmd_doctor(args: argparse.Namespace) -> int:
    """Saude do pack. Endereca achado 2.10 da auditoria F-014.

    Modo dev (repo-mae, detectado via core/manifest/):
      1. .guia/ files existem
      2. core/manifest/manifest.yaml carrega como YAML valido
      3. PyYAML disponivel
      4. git no PATH (warn, nao fatal)
      5. render --check OK (a menos que --skip-render)
      6. plugins/guia/bin/guia.py existe
      7. lock_api.py importavel

    Modo consumer (layout flat .guia-fluxo/bin/):
      1. .guia/ files existem
      4. git no PATH (warn)

    `--strict` promove warnings a erros tambem.
    """
    from _git_ops import has_git

    failures: list[str] = []
    warnings: list[str] = []

    # 1. .guia/ files (sempre). process.json e configuracao (versionada);
    # tasks/backlog/current sao estado local, que pode estar fora do git
    # (checkout limpo do CI, D-106): ausente e projeto sem demandas, nao erro.
    if not PROCESS_FILE.exists():
        failures.append(f"missing: {relative(PROCESS_FILE)}")
    for path in (TASKS_FILE, BACKLOG_FILE, CURRENT_FILE):
        if not path.exists():
            warnings.append(f"estado ausente: {relative(path)} (projeto sem demandas ou estado fora do git)")

    # 4. git (sempre)
    if not has_git():
        warnings.append("git nao encontrado no PATH (commit/worktree falharao)")

    if _is_dev_repo():
        code_root = _code_root()
        # 2 + 3. manifest + PyYAML
        manifest = code_root / "core" / "manifest" / "manifest.yaml"
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
            render = code_root / "core" / "build" / "render-skills.py"
            if render.exists():
                import subprocess

                result = subprocess.run(
                    [sys.executable, str(render), "--check"],
                    cwd=code_root,
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    failures.append(
                        "render --check falhou: plugins/guia/ stale. Rode `python core/build/render-skills.py`"
                    )

        # 6. plugins/guia/bin/guia.py
        dist_guia = code_root / "plugins" / "guia" / "bin" / "guia.py"
        if not dist_guia.exists():
            warnings.append(f"motor standalone ausente: {relative(dist_guia)}")

        # 7. lock_api importavel
        lock_api_path = code_root / "core" / "lock" / "lock_api.py"
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
    "initialize_project",
    "ensure_initialized",
    "deploy_lock_templates",
    "configure_hooks_path",
    "cmd_init",
    "cmd_status",
    "cmd_ready",
    "cmd_finish",
    "cmd_cancel",
    "cmd_block",
    "cmd_unblock",
    "cmd_upgrade",
    "cmd_plan",
    "cmd_start",
    "cmd_validate",
    "cmd_doctor",
]
