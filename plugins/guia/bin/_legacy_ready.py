"""Demanda aguardando validacao de antes do modo pr (D-180).

Quando o projeto passa a entregar por PR, as demandas que ja tinham dado
`ready` no fluxo antigo tiveram o codigo commitado direto na base. O condutor
mandava `ship` nelas - nao ha branch nem PR a abrir. O marco e o primeiro PR
do projeto: `ready` antes dele, sem PR proprio, e legado - valide e decida o
`finish` ou o `cancel` (do dono).
"""

from __future__ import annotations

from typing import Any

from _tasks import list_tasks


def first_pr_at(tasks: list[dict[str, Any]] | None = None) -> str | None:
    """Quando o primeiro PR do projeto foi aberto (None: nenhum ainda)."""
    shipped = [(t.get("pr") or {}).get("shippedAt") for t in (tasks if tasks is not None else list_tasks())]
    shipped = [at for at in shipped if at]
    return min(shipped) if shipped else None


def legacy_ready(task: dict[str, Any], tasks: list[dict[str, Any]] | None = None) -> str | None:
    """O marco (primeiro PR) se a demanda e anterior a ele, senao None."""
    ready_at = task.get("readyAt")
    if task.get("pr") or not ready_at:
        return None
    first = first_pr_at(tasks)
    return first if first and ready_at < first else None


__all__ = ["first_pr_at", "legacy_ready"]
