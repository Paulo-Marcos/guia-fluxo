"""FEATURES.md upsert and block rendering.

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
    MSG_NONE_PLACEHOLDER,
    SECTION_DONE,
    SECTION_FILES,
    SECTION_VALIDATION_DONE,
    SECTION_VALIDATION_PENDING,
)
from _state import read_text


def task_kind_label(task: dict[str, Any]) -> str:
    return KIND_LABELS.get(task.get("kind", ""), KIND_LABELS[KIND_FEATURE])


def markdown_list(values: list[str], wrap: str = "") -> list[str]:
    if not values:
        return [f"- {MSG_NONE_PLACEHOLDER}"]
    return [f"- {wrap}{value}{wrap}" for value in values]


def render_features_block(task: dict[str, Any]) -> str:
    lines = [
        f"## [{task['id']}] {task['title']}",
        "",
        f"- **Status:** {task['status']}",
        f"- **Origem:** {task.get('origin', 'AI process')}",
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


__all__ = [
    "task_kind_label",
    "markdown_list",
    "render_features_block",
    "upsert_features_entry",
]
