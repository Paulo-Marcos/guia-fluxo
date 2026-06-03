"""Centralized constants for the AI-process CLI.

Single source of truth for paths, status labels, regexes, default messages
and status-to-tag mapping. Touching a label here propagates to every
consumer (ai.py, render-skills.py, tests, future modules).

Keep this module dependency-free (stdlib only) so any module can import it
without cycles.
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


AI_DIR = ROOT / ".ai"
PROCESS_FILE = AI_DIR / "process.json"
TASKS_FILE = AI_DIR / "tasks.json"
BACKLOG_FILE = AI_DIR / "backlog.json"
CURRENT_FILE = AI_DIR / "current-task.json"
CHAT_TITLE_FILE = AI_DIR / "chat-title.txt"
DOCS_MAP_FILE = AI_DIR / "docs-map.yaml"
REPORTS_DIR = AI_DIR / "reports"
FEATURES_FILE = ROOT / "FEATURES.md"
REGISTRY_FILE = ROOT / "features" / "registry.yaml"


TASK_HEADING_RE = re.compile(r"^## \[([FI])-(\d+)\] (.+)$", re.MULTILINE)


STATUS_IN_DEVELOPMENT = "Em desenvolvimento"
STATUS_AWAITING_VALIDATION = "Aguardando validacao"
STATUS_AWAITING_VALIDATION_ACCENTED = "Aguardando validação"
STATUS_VALIDATED = "Validada"
STATUS_FINISHED = "Finalizada"
STATUS_PLANNED = "Planejada"
STATUS_BLOCKED = "Bloqueada"
STATUS_CANCELLED = "Cancelada"


STATUS_TAGS: dict[str, str] = {
    STATUS_IN_DEVELOPMENT: "DEV",
    STATUS_AWAITING_VALIDATION: "VALIDACAO",
    STATUS_AWAITING_VALIDATION_ACCENTED: "VALIDACAO",
    STATUS_VALIDATED: "FINALIZADO",
    STATUS_FINISHED: "FINALIZADO",
    STATUS_PLANNED: "PLANEJADA",
    STATUS_BLOCKED: "BLOQUEADA",
    STATUS_CANCELLED: "CANCELADA",
}


KIND_FEATURE = "feature"
KIND_ISSUE = "issue"

PREFIX_FEATURE = "F"
PREFIX_ISSUE = "I"
PREFIX_BACKLOG = "B"


MSG_TASK_NOT_FOUND = "Task not found: {id}"
MSG_NO_CURRENT_TASK = "No task id provided and no current task set."
MSG_BACKLOG_ITEM_NOT_FOUND = "Backlog item not found: {id}"
MSG_LOCK_ID_REQUIRED = "--lock-id is required when using --lock."
MSG_NO_FILES_TO_LOCK = "No files to lock. Add files with --file."
MSG_LOCK_ALREADY_EXISTS = "Lock already exists: {id}"
MSG_NO_FILES_FOR_COMMIT = "No files registered for commit."
MSG_UNRELATED_STAGED = "Unrelated staged files would be committed: {names}"
MSG_PROCESS_FILES_OK = "AI process files OK."
MSG_GIT_NOT_FOUND = (
    "git nao encontrado no PATH. Instale Git ou ajuste PATH antes de rodar este comando."
)
MSG_DEFAULT_TASK_CREATED = "Demanda criada via ai-process."
MSG_DEFAULT_READY_SUMMARY = "Implementacao entregue para validacao via ai-process."
MSG_DEFAULT_FINISH_SUMMARY = "Demanda finalizada via ai-process."
MSG_DEFAULT_VALIDATE_SUMMARY = "Validacao confirmada pelo desenvolvedor."
MSG_DEFAULT_VALIDATION_PENDING = "Validacao manual do desenvolvedor."
MSG_DEFAULT_TASK_PENDING = "Executar implementacao e validacoes."
MSG_NONE_PLACEHOLDER = "Nenhuma."
MSG_VALIDATE_DEPRECATED = (
    "AVISO: `validate` esta deprecado e sera removido em uma proxima versao. "
    "Use `finish --no-commit` para o mesmo efeito sem commit."
)


CHAT_TITLE_FORMAT_DEFAULT = "{id} - #{statusTag} - {title}"


KIND_LABELS = {
    KIND_FEATURE: "Feature",
    KIND_ISSUE: "Issue / regressao",
}


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
    "AI_DIR",
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
    "STATUS_TAGS",
    "KIND_FEATURE",
    "KIND_ISSUE",
    "PREFIX_FEATURE",
    "PREFIX_ISSUE",
    "PREFIX_BACKLOG",
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
    "SECTION_FILES",
    "SECTION_DONE",
    "SECTION_VALIDATION_DONE",
    "SECTION_VALIDATION_PENDING",
    "FEATURES_HEADER",
    "FEATURES_INSERT_MARKER",
    "MIN_PYTHON_MAJOR",
    "MIN_PYTHON_MINOR",
]
