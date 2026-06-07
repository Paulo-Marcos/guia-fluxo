"""F-010 docs hook: load .ai/docs-map.yaml, compute candidates, gate finish.

Triggers supported:
    task-finished           always fires for finish events
    touched                 fires when changed files match `paths:`
    architectural-decision  always fires (heuristic, agent decides)

Returns plain data so the CLI layer formats it.
"""

from __future__ import annotations

import argparse
import fnmatch
import sys
from typing import Any

from _clock import today
from _constants import (
    DOCS_MAP_FILE,
    MSG_NONE_PLACEHOLDER,
)
from _paths import relative


def load_docs_map() -> dict[str, Any] | None:
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


def _trigger_reason(
    kind: str | None,
    trigger: dict[str, Any],
    files: list[str],
    task: dict[str, Any],
) -> str | None:
    if kind == "task-finished":
        # ADR-0011 Fase 4: usa o kind literal da task. Tasks antigas
        # com kind=issue caem aqui (legacy-read).
        kind_label = task.get("kind") or "task"
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
        return "architectural-decision: avalie se a feature/issue mudou regra arquitetural"
    return None


def compute_docs_candidates(
    task: dict[str, Any],
    changed_files: list[str],
    docs_map: dict[str, Any],
) -> list[dict[str, str]]:
    files = list(dict.fromkeys(task.get("modifiedFiles", []) + (changed_files or [])))
    files = [f for f in files if f and f != MSG_NONE_PLACEHOLDER]
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
            kind = trigger.get("event")
            if kind is None:
                # YAML 1.1 quirk: bare `on:` parses to True. Accept only
                # string fallback to avoid masking the bug silently.
                raw_on = trigger.get("on")
                if isinstance(raw_on, str):
                    kind = raw_on
            hint = trigger.get("hint", "")
            reason = _trigger_reason(kind, trigger, files, task)
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
            break
    return candidates


def ensure_docs_review_ok(
    task: dict[str, Any],
    changed_files: list[str],
    docs_map: dict[str, Any],
    args: argparse.Namespace,
) -> None:
    candidates = compute_docs_candidates(task, changed_files, docs_map)
    if not candidates:
        return
    touched = [t for t in (getattr(args, "docs_touched", []) or []) if t]
    skipped_reason = (getattr(args, "docs_skip", "") or "").strip()
    if not touched and not skipped_reason and not getattr(args, "docs_checked", False):
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
    record: dict[str, Any] = {
        "candidates": candidates,
        "touched": [t for t in (getattr(args, "docs_touched", []) or []) if t],
        "checkedAt": today(),
    }
    skip = (getattr(args, "docs_skip", "") or "").strip()
    if skip:
        record["skipped"] = skip
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


__all__ = [
    "load_docs_map",
    "compute_docs_candidates",
    "ensure_docs_review_ok",
    "build_docs_review_record",
    "print_docs_block",
]
