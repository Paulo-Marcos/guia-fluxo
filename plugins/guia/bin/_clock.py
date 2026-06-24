"""Date/time helpers.

Isolated so tests can monkeypatch a single seam if they ever need to
freeze time. Kept tiny on purpose.
"""

from __future__ import annotations

import os
from datetime import date, datetime


def today() -> str:
    return date.today().isoformat()


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def now_iso() -> str:
    """Timestamp preciso, com timezone, em ISO-8601 (resolucao de segundos).

    D-052: seam para o timing rico (startedAt/readyAt/finishedAt e os
    intervalos de block). Distinto de `today()` (so-data, mantido para
    compat) e de `timestamp()` (formato de nome de arquivo). Honra a env
    `GUIA_NOW` para os testes congelarem o relogio sem monkeypatch atraves
    do subprocess - espelha o override `GUIA_PROJECT_ROOT` de _constants.
    """
    override = os.environ.get("GUIA_NOW")
    if override:
        return override
    return datetime.now().astimezone().isoformat(timespec="seconds")


def parse_iso(value: str | None) -> datetime | None:
    """Parse de um timestamp ISO-8601 vindo de now_iso (ou None/legado).

    Retorna None quando o valor e vazio ou nao parseavel (ex.: o so-data
    `today()` legado tambem parseia, mas tasks antigas simplesmente nao tem
    os campos novos - backfill = null). Nunca levanta."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


__all__ = ["today", "timestamp", "now_iso", "parse_iso"]
