""".guia/DEMANDAS.md upsert and block rendering.

Pure transformation + a single write. Reads the existing file, replaces
the block of `task['id']` if present (or inserts after the header marker)
and writes back.
"""

from __future__ import annotations

import re
from typing import Any

from _constants import (
    FEATURES_FILE,
    FEATURES_HEADER,
    FEATURES_INSERT_MARKER,
    KIND_FEATURE,
    KIND_LABELS,
    KIND_MARKER_FALLBACK,
    KIND_MARKERS,
    MSG_NONE_PLACEHOLDER,
    SECTION_DONE,
    SECTION_FILES,
    SECTION_TIMING,
    SECTION_VALIDATION_DONE,
    SECTION_VALIDATION_PENDING,
)
from _features_archive import archive_old_entries
from _state import read_text
from _stats import compute_stats, format_duration  # D-052


def task_kind_label(task: dict[str, Any]) -> str:
    return KIND_LABELS.get(task.get("kind", ""), KIND_LABELS[KIND_FEATURE])


def markdown_list(values: list[str], wrap: str = "") -> list[str]:
    if not values:
        return [f"- {MSG_NONE_PLACEHOLDER}"]
    return [f"- {wrap}{value}{wrap}" for value in values]


def render_timing_lines(task: dict[str, Any]) -> list[str]:
    """D-052: secao de timing (isolada para minimizar conflito com D-090).

    Retorna [] quando a task nao tem nenhum timestamp rico (pre-D-052), de
    modo que o catalogo de tasks antigas nao ganha ruido vazio."""
    stats = compute_stats(task)
    if not (stats["startedAt"] or stats["readyAt"] or stats["finishedAt"]):
        return []
    lines = [SECTION_TIMING, ""]
    lines.append(f"- **Iniciada:** {stats['startedAt'] or MSG_NONE_PLACEHOLDER}")
    lines.append(f"- **Ready:** {stats['readyAt'] or MSG_NONE_PLACEHOLDER}")
    lines.append(f"- **Terminada:** {stats['finishedAt'] or MSG_NONE_PLACEHOLDER}")
    if stats["elapsedTotalSeconds"] is not None:
        lines.append(f"- **Elapsed total:** {format_duration(stats['elapsedTotalSeconds'])}")
    if stats["activeTimeSeconds"] is not None:
        lines.append(f"- **Tempo ativo:** {format_duration(stats['activeTimeSeconds'])}")
    return lines


def render_features_block(task: dict[str, Any]) -> str:
    marker = KIND_MARKERS.get(task.get("kind", ""), KIND_MARKER_FALLBACK)
    lines = [
        f"## [{task['id']}] {marker} {task['title']}",
        "",
        f"- **Status:** {task['status']}",
        f"- **Origem:** {task.get('origin', 'Guia Fluxo')}",
        f"- **Tipo:** {task_kind_label(task)}",
        f"- **Contexto:** {task.get('context', task['title'])}",
        "",
        SECTION_FILES,
        "",
    ]
    lines.extend(markdown_list(task.get("modifiedFiles", []), "`"))
    lines.extend(["", SECTION_DONE, ""])
    lines.extend(markdown_list(task.get("summary", [])))
    lines.extend(["", SECTION_VALIDATION_DONE, ""])
    lines.extend(markdown_list(task.get("validations", [])))
    lines.extend(["", SECTION_VALIDATION_PENDING, ""])
    lines.extend(markdown_list(task.get("pending", [])))
    timing = render_timing_lines(task)  # D-052
    if timing:
        lines.append("")
        lines.extend(timing)
    lines.append("")
    lines.append("")
    return "\n".join(lines)


def upsert_features_entry(task: dict[str, Any]) -> None:
    if not FEATURES_FILE.exists():
        FEATURES_FILE.write_text(FEATURES_HEADER, encoding="utf-8")
    content = read_text(FEATURES_FILE)
    block = render_features_block(task)
    # Separador de bloco aceita D-NNN (ADR-0011 Fase 1) + legacy F/I.
    pattern = re.compile(
        rf"^## \[{re.escape(task['id'])}\].*?(?=^## \[[DFI]-\d+\] |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    if pattern.search(content):
        # Use a lambda so re.sub treats `block` as a literal: an os-path
        # like `src\editor\...` inside block would otherwise be interpreted
        # as a regex backreference (\e -> bad escape).
        content = pattern.sub(lambda _match: block, content)
    else:
        insert_at = content.find(FEATURES_INSERT_MARKER)
        if insert_at >= 0:
            insert_at += len(FEATURES_INSERT_MARKER)
            content = content[:insert_at] + block + "\n" + content[insert_at:]
        else:
            content = content.rstrip() + "\n\n" + block
    FEATURES_FILE.write_text(content, encoding="utf-8")
    # D-090: depois de gravar, mantem so as N demandas mais recentes no .md e
    # arquiva as antigas (isolado em _features_archive para merge limpo D-052).
    archive_old_entries()


__all__ = [
    "task_kind_label",
    "markdown_list",
    "render_timing_lines",
    "render_features_block",
    "upsert_features_entry",
]
