"""Date/time helpers.

Isolated so tests can monkeypatch a single seam if they ever need to
freeze time. Kept tiny on purpose.
"""

from __future__ import annotations

from datetime import date, datetime


def today() -> str:
    return date.today().isoformat()


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


__all__ = ["today", "timestamp"]
