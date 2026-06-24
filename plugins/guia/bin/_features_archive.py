"""Archive old demand blocks out of .guia/DEMANDAS.md (D-090).

DEMANDAS.md grows without bound and the agent loads the whole file into
context on every operation. This module keeps only the N most-recent demand
blocks in DEMANDAS.md and moves the older ones to a single history file under
.guia/historico/, prefixed with `ARCHIVE_MARKER` (archive=true ai-skip=true)
so the agent can detect and skip it BEFORE loading it into context.

Invariants:
- tasks.json is the authoritative source of IDs. This only rewrites the
  human-readable .md mirror; it never touches ID generation.
- Idempotent: blocks moved here leave DEMANDAS.md, so a second run finds
  nothing to move; the append also de-dupes by ID, so a block can never be
  written to the history twice.

Kept deliberately small and self-contained so it merges cleanly alongside
the parallel D-052 changes in _features_md.py.
"""

from __future__ import annotations

import re

from _constants import (
    ARCHIVE_FILE,
    ARCHIVE_HEADER,
    ARCHIVE_KEEP_DEFAULT,
    FEATURES_FILE,
    PROCESS_FILE,
)
from _state import read_json, read_text

# A demand block runs from its `## [ID]` heading to the next heading (or EOF).
# Accepts D-NNN (ADR-0011) and legacy F/I/E prefixes, matching the rest of the
# engine's block parsing.
_BLOCK_RE = re.compile(
    r"^## \[[DFIE]-\d+\].*?(?=^## \[[DFIE]-\d+\] |\Z)",
    re.MULTILINE | re.DOTALL,
)
_HEADING_ID_RE = re.compile(r"^## \[([DFIE]-\d+)\]", re.MULTILINE)


def _configured_keep() -> int:
    """Read the keep-N from process.json, falling back to the default."""
    config = read_json(PROCESS_FILE, {})
    archive = config.get("archive") if isinstance(config, dict) else None
    value = archive.get("keepInDemandas") if isinstance(archive, dict) else None
    if value is None:
        return ARCHIVE_KEEP_DEFAULT
    try:
        keep = int(value)
    except (TypeError, ValueError):
        return ARCHIVE_KEEP_DEFAULT
    return keep if keep >= 0 else ARCHIVE_KEEP_DEFAULT


def _append_to_history(blocks: list[str]) -> None:
    """Append blocks to the history file, de-duping by ID (idempotent)."""
    history = read_text(ARCHIVE_FILE) if ARCHIVE_FILE.exists() else ARCHIVE_HEADER
    seen = set(_HEADING_ID_RE.findall(history))
    additions: list[str] = []
    for block in blocks:
        match = _HEADING_ID_RE.match(block)
        if match is None or match.group(1) in seen:
            continue
        seen.add(match.group(1))
        additions.append(block)
    if not additions:
        return
    ARCHIVE_FILE.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVE_FILE.write_text(history + "".join(additions), encoding="utf-8")


def archive_old_entries(keep: int | None = None) -> None:
    """Trim DEMANDAS.md to the N newest blocks; move the rest to history.

    `keep` defaults to the process.json value (`archive.keepInDemandas`).
    No-op when DEMANDAS.md holds <= N blocks. New blocks sit at the top (the
    upsert inserts right after the header marker), so the tail of the list is
    the oldest - those are the ones archived.
    """
    if not FEATURES_FILE.exists():
        return
    if keep is None:
        keep = _configured_keep()
    if keep < 0:
        return
    content = read_text(FEATURES_FILE)
    blocks = list(_BLOCK_RE.finditer(content))
    if len(blocks) <= keep:
        return
    prefix = content[: blocks[0].start()]
    kept = "".join(match.group(0) for match in blocks[:keep])
    old = [match.group(0) for match in blocks[keep:]]
    # History first: if the trim write fails, the blocks are already preserved.
    _append_to_history(old)
    FEATURES_FILE.write_text(prefix + kept, encoding="utf-8")


__all__ = ["archive_old_entries"]
