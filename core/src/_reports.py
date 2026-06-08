"""Write per-event task reports under .guia/reports/."""

from __future__ import annotations

from typing import Any

from _clock import timestamp
from _constants import REPORTS_DIR
from _features_md import render_features_block


def write_report(task: dict[str, Any], event: str) -> None:
    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / f"{task['id']}-{event}-{timestamp()}.md"
    path.write_text(render_features_block(task), encoding="utf-8")


__all__ = ["write_report"]
