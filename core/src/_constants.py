"""Centralized constants for the Guia Fluxo CLI.

Single source of truth for paths, status labels, regexes, default messages
and status-to-tag mapping. Touching a label here propagates to every
consumer (guia.py, render-skills.py, tests, future modules).

Keep this module dependency-free (stdlib only) so any module can import it
without cycles.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

# D-109 (R1): como o codigo chega a main. "direct" = commit do finish na
# arvore atual (comportamento historico); "pr" = worktree por demanda, PR e
# squash, com o estado so na arvore principal.
DELIVERY_MODE_DIRECT = "direct"
DELIVERY_MODE_PR = "pr"
DELIVERY_MODES = (DELIVERY_MODE_DIRECT, DELIVERY_MODE_PR)
# D-112 (R1): branch base do projeto, contra a qual se medem os arquivos da
# demanda (adicao/modificacao/delecao para as travas).
DELIVERY_BASE_BRANCH_DEFAULT = "main"
# D-112 (R1 commit.format): "legacy" e o header historico `kind(ID): titulo`
# com o rodape `Task:`; "gitmoji-conventional" e `<emoji> <tipo>(ID): titulo`
# com as marcas [unlock:] e o Co-Authored-By no fim.
COMMIT_FORMAT_LEGACY = "legacy"
COMMIT_FORMAT_GITMOJI = "gitmoji-conventional"
COMMIT_GITMOJI_BY_KIND = {
    "feature": "✨ feat",
    "bug": "🐛 fix",
    "issue": "🐛 fix",
    "chore": "🧹 chore",
    "epic": "🎯 chore",
}


def _linked_worktree_main(root: Path) -> Path | None:
    """Arvore principal de `root`, quando `root` e um worktree ligado do git.

    Worktree ligado tem `.git` como arquivo (`gitdir: <comum>/worktrees/<n>`)
    e o gitdir dele tem `commondir`, que aponta o `.git` comum; a arvore
    principal e a pasta dona desse `.git`. Le arquivos em vez de chamar o
    `git` porque roda no import. Submodulo (`.git` arquivo sem `commondir`),
    repo comum e repo bare devolvem None.
    """
    dot_git = root / ".git"
    if not dot_git.is_file():
        return None
    try:
        text = dot_git.read_text(encoding="utf-8").strip()
        if not text.startswith("gitdir:"):
            return None
        gitdir = Path(text[len("gitdir:"):].strip())
        if not gitdir.is_absolute():
            gitdir = root / gitdir
        commondir_file = gitdir / "commondir"
        if not commondir_file.is_file():
            return None
        common = Path(commondir_file.read_text(encoding="utf-8").strip())
    except OSError:
        return None
    if not common.is_absolute():
        common = gitdir / common
    common = common.resolve()
    return common.parent if common.name == ".git" else None


def _delivery_mode(root: Path) -> str:
    """`delivery.mode` do `.guia/process.json` de `root`; padrao `direct`."""
    try:
        data = json.loads((root / ".guia" / "process.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return DELIVERY_MODE_DIRECT
    delivery = data.get("delivery") if isinstance(data, dict) else None
    mode = delivery.get("mode") if isinstance(delivery, dict) else None
    return mode if mode in DELIVERY_MODES else DELIVERY_MODE_DIRECT


def _state_root(candidate: Path) -> Path:
    """No modo `pr`, troca um worktree ligado pela arvore principal (R3).

    O estado (tasks, backlog, current-task) e local e mora so na principal;
    o `.guia/` do worktree tem so a configuracao versionada. Sem o desvio, o
    motor criaria ali uma copia orfa. O modo vem do `process.json` da
    principal, que e o estado autoritativo. No `direct`, nada muda.
    """
    main = _linked_worktree_main(candidate)
    if main is not None and _delivery_mode(main) == DELIVERY_MODE_PR:
        return main
    return candidate


def _resolve_root() -> Path:
    """Resolve the project root that holds `.guia/`.

    Three layers, in order:

    1. `GUIA_PROJECT_ROOT` env override (explicit; used by tests and edge
       cases).
    2. Script-relative root (`__file__`'s grandparent) when it already
       contains a `.guia/`. Keeps the historical behavior for layouts where
       the engine lives inside the project tree: the source repo
       (`core/src/`), the dogfood `plugins/guia/bin/`, and the manual-copy
       consumer (`.guia-fluxo/bin/`). Stable regardless of the current directory.
    3. Caller's working directory otherwise. This is the Claude Code plugin
       case (D-075): the engine runs from the plugin cache
       (`${CLAUDE_PLUGIN_ROOT}/bin/`), outside the consumer project, so the
       root must come from where the command was invoked. A virgin project
       (no `.guia/` yet) roots at the CWD and the auto-init seeds `.guia/`
       there.

       Deliberately the CWD exactly, with no walk up to an ancestor
       `.guia/`: an ancestor search would hijack the root to an unrelated
       project whose `.guia/` happens to sit above the CWD (e.g. a stray
       `.guia/` in the temp dir or the user's home), the same footgun
       `git`'s upward `.git` search has. Run commands from the project root.

    Layers 2 and 3 then pass through `_state_root` (D-109): in `pr` mode a
    linked worktree resolves to the main working tree. The env override is
    explicit and is never redirected.
    """
    override = os.environ.get("GUIA_PROJECT_ROOT")
    if override:
        return Path(override).resolve()

    script_root = Path(__file__).resolve().parents[2]
    if (script_root / ".guia").is_dir():
        return _state_root(script_root)

    return _state_root(Path.cwd().resolve())


ROOT = _resolve_root()
# Modo de entrega do projeto (D-109/D-110), lido do process.json da raiz do estado.
DELIVERY_MODE = _delivery_mode(ROOT)


GUIA_DIR = ROOT / ".guia"
PROCESS_FILE = GUIA_DIR / "process.json"
TASKS_FILE = GUIA_DIR / "tasks.json"
BACKLOG_FILE = GUIA_DIR / "backlog.json"
CURRENT_FILE = GUIA_DIR / "current-task.json"
# D-093: titulo da DEMANDA corrente (nao do chat). O chat pode conter varias
# demandas (epico D-049) e nao e renomeado automaticamente - a renomeacao virou
# acao opcional/manual do usuario. Mantido como pointer estavel, host-agnostico,
# que um helper externo de rename pode ler. Renomeado de chat-title.txt.
DEMAND_TITLE_FILE = GUIA_DIR / "demand-title.txt"
DOCS_MAP_FILE = GUIA_DIR / "docs-map.yaml"
REPORTS_DIR = GUIA_DIR / "reports"
# Catalogo legivel de demandas. D-055: renomeado de FEATURES.md (nome nao
# refletia a realidade - guarda feature/bug/chore) e movido para dentro de
# .guia/ (raiz do consumidor fica so com .guia/). O nome da constante segue
# FEATURES_FILE por compatibilidade interna.
FEATURES_FILE = GUIA_DIR / "DEMANDAS.md"
# Path do catalogo relativo a ROOT (POSIX). D-055: agora que o catalogo vive
# em .guia/, o basename ("DEMANDAS.md") nao basta para `modifiedFiles` e para
# a exclusao de lock - o git stageia ".guia/DEMANDAS.md". Use sempre este.
FEATURES_REL = FEATURES_FILE.relative_to(ROOT).as_posix()
REGISTRY_FILE = GUIA_DIR / "locks" / "registry.yaml"
# D-090: DEMANDAS.md cresce sem limite e o agente carrega tudo a cada operacao.
# Mantemos so as N demandas mais recentes no .md; as antigas migram para o
# arquivo de historico abaixo, marcado com ARCHIVE_MARKER (ai-skip) para o
# agente nao puxar para o contexto. tasks.json continua a fonte de IDs - o
# arquivamento do .md nunca afeta a geracao do proximo ID.
ARCHIVE_DIR = GUIA_DIR / "historico"
ARCHIVE_FILE = ARCHIVE_DIR / "DEMANDAS.md"
ARCHIVE_MARKER = "<!-- guia-fluxo: archive=true ai-skip=true -->"
ARCHIVE_HEADER = f"{ARCHIVE_MARKER}\n# Demandas (historico)\n\n---\n\n"
ARCHIVE_KEEP_DEFAULT = 30


# Aceita IDs novos (D-NNN per ADR-0011) e legacy (F-NNN, I-NNN).
# B-NNN entra na Fase 2 quando backlog for absorvido em tasks.json.
TASK_HEADING_RE = re.compile(r"^## \[([DFIE])-(\d+)\] (.+)$", re.MULTILINE)


STATUS_IN_DEVELOPMENT = "Em desenvolvimento"
STATUS_AWAITING_VALIDATION = "Aguardando validacao"
STATUS_AWAITING_VALIDATION_ACCENTED = "Aguardando validação"
STATUS_VALIDATED = "Validada"
STATUS_FINISHED = "Finalizada"
STATUS_BACKLOG = "Backlog"
STATUS_PLANNED = "Planejada"
STATUS_BLOCKED = "Bloqueada"
STATUS_CANCELLED = "Cancelada"
# D-122 (R3): modo `pr` - branch empurrada e PR aberto; CI e auditoria correndo.
STATUS_IN_PR = "Em PR"
# D-126 (R3): auditada e enfileirada; o executor integra na ordem.
STATUS_IN_QUEUE = "Na fila"
# D-127 (R3): mergeado pelo executor; o finish fecha depois da validacao.
STATUS_INTEGRATED = "Integrada"
# Item de backlog ja entregue por outra demanda (ou obsoleto): retirado da
# lista ativa via `backlog resolve`, mas preservado no arquivo para historico.
STATUS_RESOLVED = "Resolvida"


STATUS_TAGS: dict[str, str] = {
    STATUS_IN_DEVELOPMENT: "DEV",
    STATUS_AWAITING_VALIDATION: "VALIDACAO",
    STATUS_AWAITING_VALIDATION_ACCENTED: "VALIDACAO",
    STATUS_VALIDATED: "FINALIZADO",
    STATUS_FINISHED: "FINALIZADO",
    STATUS_BACKLOG: "BACKLOG",
    STATUS_PLANNED: "PLANEJADA",
    STATUS_BLOCKED: "BLOQUEADA",
    STATUS_CANCELLED: "CANCELADA",
    STATUS_IN_PR: "PR",
    STATUS_IN_QUEUE: "FILA",
    STATUS_INTEGRATED: "INTEGRADA",
    STATUS_RESOLVED: "RESOLVIDA",
}


# Kind novos (ADR-0011). KIND_ISSUE preservado para resolver tasks legacy
# (I-NNN). Fase 4 remove `issue` como verbo/skill; aqui ele continua
# legivel para que tasks antigas renderizem em .guia/DEMANDAS.md.
KIND_FEATURE = "feature"
KIND_BUG = "bug"
KIND_CHORE = "chore"
KIND_ISSUE = "issue"  # legacy-read only; nao gerar tasks novas com este kind a partir da Fase 4.
# D-049: Epic e o agregador de stories. Tem prefixo proprio E-NNN e
# numeracao independente de D-NNN (leitura instantanea de epico vs story).
KIND_EPIC = "epic"

# Prefixo neutro do ADR-0011 para todas as tasks novas.
# PREFIX_FEATURE/ISSUE/BACKLOG permanecem para resolver IDs antigos.
PREFIX_DEMANDA = "D"
PREFIX_FEATURE = "F"
PREFIX_ISSUE = "I"
PREFIX_BACKLOG = "B"
PREFIX_EPIC = "E"  # D-049

# Prefixos considerados quando next_task_id calcula o proximo numero.
# Garante numeracao monotonica unica visualmente (D-030 nao colide com
# F-029 ja existente).
TASK_PREFIXES_FOR_NUMBERING = (PREFIX_DEMANDA, PREFIX_FEATURE, PREFIX_ISSUE)


MSG_TASK_NOT_FOUND = "Task not found: {id}"
MSG_NO_CURRENT_TASK = "No task id provided and no current task set."
MSG_BACKLOG_ITEM_NOT_FOUND = "Backlog item not found: {id}"
MSG_BACKLOG_ALREADY_RESOLVED = "{id} ja esta resolvido (status=Resolvida)."
MSG_BACKLOG_RESOLVED = "{id} resolvido e retirado do backlog ativo."
# D-067: status que "satisfazem" uma dependencia (a task dependente pode
# avancar). Inclui terminais nao-Cancelada e Resolvida (D-079). Cancelada
# tambem satisfaz: a dep foi explicitamente terminada; bloquear a
# dependente forcaria a re-abrir a dep cancelada (workflow ruim).
STATUSES_SATISFY_DEPENDENCY = frozenset({
    "Validada", "Finalizada", "Resolvida", "Cancelada",
})
MSG_LOCK_ID_REQUIRED = "--lock-id is required when using --lock."
MSG_NO_FILES_TO_LOCK = "No files to lock. Add files with --file."
MSG_LOCK_ALREADY_EXISTS = "Lock already exists: {id}"
MSG_NO_FILES_FOR_COMMIT = "No files registered for commit."
MSG_UNRELATED_STAGED = "Unrelated staged files would be committed: {names}"
MSG_PROCESS_FILES_OK = "Guia Fluxo files OK."
MSG_GIT_NOT_FOUND = (
    "git nao encontrado no PATH. Instale Git ou ajuste PATH antes de rodar este comando."
)
MSG_DEFAULT_TASK_CREATED = "Demanda criada via Guia Fluxo."
MSG_DEFAULT_READY_SUMMARY = "Implementacao entregue para validacao via Guia Fluxo."
MSG_DEFAULT_FINISH_SUMMARY = "Demanda finalizada via Guia Fluxo."
MSG_DEFAULT_VALIDATE_SUMMARY = "Validacao confirmada pelo desenvolvedor."
MSG_DEFAULT_VALIDATION_PENDING = "Validacao manual do desenvolvedor."
MSG_DEFAULT_TASK_PENDING = "Executar implementacao e validacoes."
MSG_NONE_PLACEHOLDER = "Nenhuma."
MSG_VALIDATE_DEPRECATED = (
    "AVISO: `validate` esta deprecado e sera removido em uma proxima versao. "
    "Use `finish --no-commit` para o mesmo efeito sem commit."
)
# D-095: `finish` exige uma validacao consultiva de qualidade do que foi feito
# antes de fechar (alem dos comandos de teste). Skills sao acionadas pelo
# AGENTE, nao pelo Python, entao o core sinaliza+exige e a skill `guia:finish`
# executa. Estas listas alimentam o bloco instrutivo do gate (_quality_hook).
QUALITY_DIMENSIONS = (
    "(a) qualidade do codigo (legibilidade, nomes, clean code)",
    "(b) tamanho de funcoes/arquivos (funcao curta, arquivo coeso)",
    "(c) responsabilidade unica (SRP) por funcao/classe/modulo",
    "(d) cobertura/tests do que mudou",
    "(e) necessidade de refatorar para boa qualidade - e refatorar antes de fechar",
)
QUALITY_SKILL_SUGGESTIONS = (
    "clean-code-review",
    "clean-architecture-guardian",
    "tdd-dotnet",
    "valida-pasta (D-085, quando disponivel)",
)


DEMAND_TITLE_FORMAT_DEFAULT = "{id} {kindMarker} - #{statusTag} - {title}"


KIND_LABELS = {
    KIND_FEATURE: "Feature",
    KIND_BUG: "Bug / regressao",
    KIND_CHORE: "Chore",
    KIND_ISSUE: "Bug (legacy)",  # Compat para tasks antigas com kind=issue.
    KIND_EPIC: "Epic",  # D-049: agregador de stories.
}

# Marcadores visuais (emoji) que aparecem ao lado do ID em todas as
# superficies de display (demand-title, tasks list, backlog list, headings
# de .guia/DEMANDAS.md). ID continua neutro (D-NNN) per ADR-0011; o emoji da
# o sinal visual de qual kind a demanda e.
KIND_MARKERS = {
    KIND_FEATURE: "✨",
    KIND_BUG: "🐛",
    KIND_CHORE: "🧹",
    KIND_ISSUE: "🐛",  # legacy = bug.
    KIND_EPIC: "🎯",  # D-049: epic.
}

# Fallback para tasks sem kind ou kind desconhecido. Quase nunca dispara
# (cmd_create_task sempre seta kind), mas mantemos para resiliencia.
KIND_MARKER_FALLBACK = "•"


SECTION_FILES = "### Arquivos modificados/criados"
SECTION_DONE = "### O que foi feito"
SECTION_VALIDATION_DONE = "### Validacao feita"
SECTION_VALIDATION_PENDING = "### Validacao pendente"
# D-052: secao opcional de timing no catalogo/reports - so aparece quando a
# task tem ao menos um timestamp rico (tasks pre-D-052 nao renderizam isto).
SECTION_TIMING = "### Timing (D-052)"
FEATURES_HEADER = "# Demandas\n\n---\n\n"
FEATURES_INSERT_MARKER = "---\n\n"

# D-052: schemaVersion do tasks.json bumpado para 2 (campos de timing
# startedAt/readyAt/finishedAt + blocks[].blockedAt/unblockedAt + readyCount).
# Migracao e aditiva: tasks antigas seguem sem os campos (backfill = null),
# nenhuma logica ramifica no numero - ele e informativo/rastreavel.
TASKS_SCHEMA_VERSION = 2


MIN_PYTHON_MAJOR = 3
MIN_PYTHON_MINOR = 10


__all__ = [
    "ROOT",
    "COMMIT_FORMAT_GITMOJI",
    "COMMIT_FORMAT_LEGACY",
    "COMMIT_GITMOJI_BY_KIND",
    "DELIVERY_BASE_BRANCH_DEFAULT",
    "DELIVERY_MODE",
    "STATUS_IN_PR",
    "STATUS_IN_QUEUE",
    "STATUS_INTEGRATED",
    "DELIVERY_MODE_DIRECT",
    "DELIVERY_MODE_PR",
    "DELIVERY_MODES",
    "GUIA_DIR",
    "PROCESS_FILE",
    "TASKS_FILE",
    "BACKLOG_FILE",
    "CURRENT_FILE",
    "DEMAND_TITLE_FILE",
    "DOCS_MAP_FILE",
    "REPORTS_DIR",
    "FEATURES_FILE",
    "FEATURES_REL",
    "REGISTRY_FILE",
    "ARCHIVE_DIR",
    "ARCHIVE_FILE",
    "ARCHIVE_MARKER",
    "ARCHIVE_HEADER",
    "ARCHIVE_KEEP_DEFAULT",
    "TASK_HEADING_RE",
    "STATUS_IN_DEVELOPMENT",
    "STATUS_AWAITING_VALIDATION",
    "STATUS_VALIDATED",
    "STATUS_BACKLOG",
    "STATUS_PLANNED",
    "STATUS_BLOCKED",
    "STATUS_CANCELLED",
    "STATUS_TAGS",
    "KIND_FEATURE",
    "KIND_BUG",
    "KIND_CHORE",
    "KIND_ISSUE",
    "KIND_EPIC",
    "PREFIX_DEMANDA",
    "PREFIX_FEATURE",
    "PREFIX_ISSUE",
    "PREFIX_BACKLOG",
    "PREFIX_EPIC",
    "TASK_PREFIXES_FOR_NUMBERING",
    "MSG_TASK_NOT_FOUND",
    "MSG_NO_CURRENT_TASK",
    "MSG_BACKLOG_ITEM_NOT_FOUND",
    "STATUSES_SATISFY_DEPENDENCY",
    "MSG_LOCK_ID_REQUIRED",
    "MSG_NO_FILES_TO_LOCK",
    "MSG_LOCK_ALREADY_EXISTS",
    "MSG_NO_FILES_FOR_COMMIT",
    "MSG_UNRELATED_STAGED",
    "MSG_PROCESS_FILES_OK",
    "MSG_GIT_NOT_FOUND",
    "MSG_DEFAULT_TASK_CREATED",
    "MSG_DEFAULT_READY_SUMMARY",
    "MSG_DEFAULT_FINISH_SUMMARY",
    "MSG_DEFAULT_VALIDATE_SUMMARY",
    "MSG_DEFAULT_VALIDATION_PENDING",
    "MSG_DEFAULT_TASK_PENDING",
    "MSG_NONE_PLACEHOLDER",
    "MSG_VALIDATE_DEPRECATED",
    "QUALITY_DIMENSIONS",
    "QUALITY_SKILL_SUGGESTIONS",
    "DEMAND_TITLE_FORMAT_DEFAULT",
    "KIND_LABELS",
    "KIND_MARKERS",
    "KIND_MARKER_FALLBACK",
    "SECTION_FILES",
    "SECTION_DONE",
    "SECTION_VALIDATION_DONE",
    "SECTION_VALIDATION_PENDING",
    "SECTION_TIMING",
    "TASKS_SCHEMA_VERSION",
    "FEATURES_HEADER",
    "FEATURES_INSERT_MARKER",
    "MIN_PYTHON_MAJOR",
    "MIN_PYTHON_MINOR",
]
