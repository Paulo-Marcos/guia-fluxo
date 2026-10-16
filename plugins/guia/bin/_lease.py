"""O lease do executor da fila (D-127), lido por quem nao e o executor (D-176).

O executor escreve `executor.lease` (pid, host, batimento) e o renova a cada
passada. O chat le o mesmo arquivo para saber se ha alguem integrando: com
executor vivo, o `queue add` e o fim do chat; sem ele, quem destrava e o dono.
Modulo sem dependencias pesadas - o condutor o importa a cada `next`.
"""

from __future__ import annotations

import json
import time
from typing import Any

from _constants import GUIA_DIR

LEASE_FILE = GUIA_DIR / "queue" / "executor.lease"
LEASE_STALE_MINUTES_DEFAULT = 10


def read_lease() -> dict[str, Any] | None:
    try:
        return json.loads(LEASE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def stale_minutes(config: dict[str, Any]) -> float:
    queue_cfg = (config.get("delivery") or {}).get("queue") or {}
    return float(queue_cfg.get("leaseStaleMinutes") or LEASE_STALE_MINUTES_DEFAULT)


def executor_status(config: dict[str, Any]) -> dict[str, Any] | None:
    """O executor vivo (pid, host, idade do batimento em s) ou None.

    Batimento mais velho que `leaseStaleMinutes` conta como morto: e o mesmo
    criterio que o `acquire_lease` usa para tomar o lease de volta.
    """
    lease = read_lease()
    if not lease:
        return None
    age = time.time() - float(lease.get("heartbeat") or 0)
    if age >= stale_minutes(config) * 60:
        return None
    return {"pid": lease.get("pid"), "host": lease.get("host"), "age": round(max(age, 0))}


def describe_executor(config: dict[str, Any]) -> str:
    alive = executor_status(config)
    if alive:
        return (f"executor ativo (pid {alive['pid']} em {alive['host']}, batimento ha {alive['age']}s): "
                "ele integra, limpa e fecha - fim do chat")
    return "sem executor ativo: peca ao dono o `guia queue run`"


__all__ = ["LEASE_FILE", "LEASE_STALE_MINUTES_DEFAULT", "describe_executor", "executor_status", "read_lease", "stale_minutes"]
