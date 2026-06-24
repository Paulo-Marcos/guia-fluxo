"""D-052: throughput stats derivadas dos timestamps ricos de uma task.

Funcoes puras sobre o dict da task. Timestamps ausentes (tasks criadas
antes do D-052, ou que ainda nao atingiram o estado relevante) viram
`None` - nunca inventamos valores (backfill = null). Sem I/O.

Campos consumidos:
    startedAt   - entrada em "Em desenvolvimento" (set/start/promote)
    readyAt     - ultima vez que rodou `ready`
    finishedAt  - estado terminal (Validada/Finalizada/Cancelada)
    blocks[]    - cada bloqueio com blockedAt + unblockedAt
    readyCount  - numero de ciclos ready
"""

from __future__ import annotations

from typing import Any

from _clock import parse_iso


def _delta_seconds(start: str | None, end: str | None) -> int | None:
    """Segundos entre dois timestamps ISO, ou None se algum faltar/for invalido."""
    begin = parse_iso(start)
    finish = parse_iso(end)
    if begin is None or finish is None:
        return None
    return int((finish - begin).total_seconds())


def elapsed_blocked_seconds(task: dict[str, Any]) -> int | None:
    """Soma dos intervalos de bloqueio fechados (unblockedAt - blockedAt).

    Considera apenas blocks com os dois timestamps presentes. Retorna None
    quando nenhum block contribuiu (task nunca bloqueada, ou blocks legados
    sem os campos novos), preservando a distincao "0 segundos bloqueado"
    (houve block instantaneo) de "sem dado de bloqueio".
    """
    total = 0
    counted = False
    for block in task.get("blocks") or []:
        delta = _delta_seconds(block.get("blockedAt"), block.get("unblockedAt"))
        if delta is not None:
            total += delta
            counted = True
    return total if counted else None


def compute_stats(task: dict[str, Any]) -> dict[str, Any]:
    """Snapshot de timing/throughput. Wall-clock e active-time em segundos.

    elapsedTotal = finishedAt - startedAt (inclui pausas).
    activeTime   = elapsedTotal - elapsedBlocked (desconta pausas fechadas).
    """
    started = task.get("startedAt")
    ready = task.get("readyAt")
    finished = task.get("finishedAt")
    elapsed_total = _delta_seconds(started, finished)
    elapsed_blocked = elapsed_blocked_seconds(task)
    active_time: int | None = None
    if elapsed_total is not None:
        active_time = elapsed_total - (elapsed_blocked or 0)
    blocks = task.get("blocks") or []
    return {
        "startedAt": started,
        "readyAt": ready,
        "finishedAt": finished,
        "elapsedTotalSeconds": elapsed_total,
        "elapsedBlockedSeconds": elapsed_blocked,
        "activeTimeSeconds": active_time,
        "blockCount": len(blocks),
        "unblockCount": sum(1 for b in blocks if b.get("unblockedAt")),
        "readyCount": task.get("readyCount", 0),
    }


def format_duration(seconds: int | None) -> str:
    """Duracao legivel (ex.: `2h 03m 04s`). `-` quando o dado nao existe."""
    if seconds is None:
        return "-"
    sign = "-" if seconds < 0 else ""
    seconds = abs(seconds)
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    parts: list[str] = []
    if hours:
        parts.append(f"{hours}h")
    if hours or minutes:
        parts.append(f"{minutes:02d}m")
    parts.append(f"{secs:02d}s")
    return sign + " ".join(parts)


__all__ = [
    "compute_stats",
    "elapsed_blocked_seconds",
    "format_duration",
]
