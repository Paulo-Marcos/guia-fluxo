"""Centralized constants for the Guia Fluxo CLI.

Single source of truth for paths, status labels, regexes, default messages
and status-to-tag mapping. Touching a label here propagates to every
consumer (guia.py, render-skills.py, tests, future modules).

Keep this module dependency-free (stdlib only) so any module can import it
without cycles.
"""

from __future__ import annotations

import os
import re
from pathlib import Path


def _resolve_root() -> Path:
    """Resolve the project root that holds `.guia/`.

    Three layers, in order:

    1. `GUIA_PROJECT_ROOT` env override (explicit; used by tests and edge
       cases).
    2. Script-relative root (`__file__`'s grandparent) when it already
       contains a `.guia/`. Keeps the historical behavior for layouts where
       the engine lives inside the project tree: the source repo
       (`core/src/`), the dogfood `dist/bin/`, and the `install.sh` consumer
       (`.guia-fluxo/bin/`). Stable regardless of the current directory.
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
    """
    override = os.environ.get("GUIA_PROJECT_ROOT")
    if override:
        return Path(override).resolve()

    script_root = Path(__file__).resolve().parents[2]
    if (script_root / ".guia").is_dir():
        return script_root

    return Path.cwd().resolve()


ROOT = _resolve_root()


GUIA_DIR = ROOT / ".guia"
PROCESS_FILE = GUIA_DIR / "process.json"
TASKS_FILE = GUIA_DIR / "tasks.json"
BACKLOG_FILE = GUIA_DIR / "backlog.json"
CURRENT_FILE = GUIA_DIR / "current-task.json"
CHAT_TITLE_FILE = GUIA_DIR / "chat-title.txt"
DOCS_MAP_FILE = GUIA_DIR / "docs-map.yaml"
REPORTS_DIR = GUIA_DIR / "reports"
FEATURES_FILE = ROOT / "FEATURES.md"
REGISTRY_FILE = ROOT / "features" / "registry.yaml"


# Aceita IDs novos (D-NNN per ADR-0011) e legacy (F-NNN, I-NNN).
# B-NNN entra na Fase 2 quando backlog for absorvido em tasks.json.
TASK_HEADING_RE = re.compile(r"^## \[([DFI])-(\d+)\] (.+)$", re.MULTILINE)


STATUS_IN_DEVELOPMENT = "Em desenvolvimento"
STATUS_AWAITING_VALIDATION = "Aguardando validacao"
STATUS_AWAITING_VALIDATION_ACCENTED = "Aguardando validação"
STATUS_VALIDATED = "Validada"
STATUS_FINISHED = "Finalizada"
STATUS_BACKLOG = "Backlog"
STATUS_PLANNED = "Planejada"
STATUS_BLOCKED = "Bloqueada"
STATUS_CANCELLED = "Cancelada"


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
}


# Kind novos (ADR-0011). KIND_ISSUE preservado para resolver tasks legacy
# (I-NNN). Fase 4 remove `issue` como verbo/skill; aqui ele continua
# legivel para que tasks antigas renderizem em FEATURES.md.
KIND_FEATURE = "feature"
KIND_BUG = "bug"
KIND_CHORE = "chore"
KIND_ISSUE = "issue"  # legacy-read only; nao gerar tasks novas com este kind a partir da Fase 4.

# Prefixo neutro do ADR-0011 para todas as tasks novas.
# PREFIX_FEATURE/ISSUE/BACKLOG permanecem para resolver IDs antigos.
PREFIX_DEMANDA = "D"
PREFIX_FEATURE = "F"
PREFIX_ISSUE = "I"
PREFIX_BACKLOG = "B"

# Prefixos considerados quando next_task_id calcula o proximo numero.
# Garante numeracao monotonica unica visualmente (D-030 nao colide com
# F-029 ja existente).
TASK_PREFIXES_FOR_NUMBERING = (PREFIX_DEMANDA, PREFIX_FEATURE, PREFIX_ISSUE)


MSG_TASK_NOT_FOUND = "Task not found: {id}"
MSG_NO_CURRENT_TASK = "No task id provided and no current task set."
MSG_BACKLOG_ITEM_NOT_FOUND = "Backlog item not found: {id}"
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


CHAT_TITLE_FORMAT_DEFAULT = "{id} {kindMarker} - #{statusTag} - {title}"


KIND_LABELS = {
    KIND_FEATURE: "Feature",
    KIND_BUG: "Bug / regressao",
    KIND_CHORE: "Chore",
    KIND_ISSUE: "Bug (legacy)",  # Compat para tasks antigas com kind=issue.
}

# Marcadores visuais (emoji) que aparecem ao lado do ID em todas as
# superficies de display (chat-title, tasks list, backlog list, headings
# de FEATURES.md). ID continua neutro (D-NNN) per ADR-0011; o emoji da
# o sinal visual de qual kind a demanda e.
KIND_MARKERS = {
    KIND_FEATURE: "✨",
    KIND_BUG: "🐛",
    KIND_CHORE: "🧹",
    KIND_ISSUE: "🐛",  # legacy = bug.
}

# Fallback para tasks sem kind ou kind desconhecido. Quase nunca dispara
# (cmd_create_task sempre seta kind), mas mantemos para resiliencia.
KIND_MARKER_FALLBACK = "•"


SECTION_FILES = "### Arquivos modificados/criados"
SECTION_DONE = "### O que foi feito"
SECTION_VALIDATION_DONE = "### Validacao feita"
SECTION_VALIDATION_PENDING = "### Validacao pendente"
FEATURES_HEADER = "# Features e Issues\n\n---\n\n"
FEATURES_INSERT_MARKER = "---\n\n"


MIN_PYTHON_MAJOR = 3
MIN_PYTHON_MINOR = 10


__all__ = [
    "ROOT",
    "GUIA_DIR",
    "PROCESS_FILE",
    "TASKS_FILE",
    "BACKLOG_FILE",
    "CURRENT_FILE",
    "CHAT_TITLE_FILE",
    "DOCS_MAP_FILE",
    "REPORTS_DIR",
    "FEATURES_FILE",
    "REGISTRY_FILE",
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
    "PREFIX_DEMANDA",
    "PREFIX_FEATURE",
    "PREFIX_ISSUE",
    "PREFIX_BACKLOG",
    "TASK_PREFIXES_FOR_NUMBERING",
    "MSG_TASK_NOT_FOUND",
    "MSG_NO_CURRENT_TASK",
    "MSG_BACKLOG_ITEM_NOT_FOUND",
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
    "CHAT_TITLE_FORMAT_DEFAULT",
    "KIND_LABELS",
    "KIND_MARKERS",
    "KIND_MARKER_FALLBACK",
    "SECTION_FILES",
    "SECTION_DONE",
    "SECTION_VALIDATION_DONE",
    "SECTION_VALIDATION_PENDING",
    "FEATURES_HEADER",
    "FEATURES_INSERT_MARKER",
    "MIN_PYTHON_MAJOR",
    "MIN_PYTHON_MINOR",
]
