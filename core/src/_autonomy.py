"""Niveis de autonomia por demanda (D-133, R6).

    manual < pr < queue < pilot

`manual`: implementa e da `ready` (o comportamento de sempre). `pr`: + ship e
audit. `queue`: + enfileira ja aprovado (D-134). `pilot`: + fecha a demanda
sozinho quando a R7 deixa (D-135). O nivel mora na demanda, nao na sessao;
sem nivel, vale `autonomy.default` (sem config, `manual`). O teto
`autonomy.ceiling` e do projeto. Subir e so do usuario, descer qualquer um.
O motor nao distingue pessoa de agente (a mesma limitacao da D-098 no
finish): quem chama declara `--by`, e a trava de verdade e o comando de plugin
so do usuario (D-136).
"""

from __future__ import annotations

from typing import Any

from _clock import now_iso

LEVELS = ("manual", "pr", "queue", "pilot")
LEVEL_DEFAULT = "manual"
CEILING_DEFAULT = "pilot"
BY_USER = "user"
BY_AGENT = "agent"


def rank(level: str) -> int:
    return LEVELS.index(level)


def settings(config: dict[str, Any]) -> dict[str, str]:
    autonomy = config.get("autonomy") or {}
    default = autonomy.get("default") if autonomy.get("default") in LEVELS else LEVEL_DEFAULT
    ceiling = autonomy.get("ceiling") if autonomy.get("ceiling") in LEVELS else CEILING_DEFAULT
    return {"default": default, "ceiling": ceiling}


def effective_level(task: dict[str, Any], config: dict[str, Any]) -> str:
    """Nivel da demanda (ou o padrao do projeto), limitado pelo teto."""
    conf = settings(config)
    level = (task.get("autonomy") or {}).get("level")
    level = level if level in LEVELS else conf["default"]
    return LEVELS[min(rank(level), rank(conf["ceiling"]))]


def set_level(task: dict[str, Any], level: str, by: str, config: dict[str, Any]) -> dict[str, Any]:
    if level not in LEVELS:
        raise SystemExit(f"Nivel invalido {level!r}: use {', '.join(LEVELS)}.")
    conf = settings(config)
    if rank(level) > rank(conf["ceiling"]):
        raise SystemExit(
            f"{level!r} esta acima do teto do projeto ({conf['ceiling']!r}, autonomy.ceiling): recusado."
        )
    current = effective_level(task, config)
    if by != BY_USER and rank(level) > rank(current):
        raise SystemExit(
            f"Subir o nivel ({current} -> {level}) e do usuario: o agente so pode descer. "
            "Peca ao usuario o /guia:autonomy."
        )
    task["autonomy"] = {"level": level, "setBy": by, "at": now_iso()}
    return task["autonomy"]


__all__ = ["BY_AGENT", "BY_USER", "LEVELS", "effective_level", "rank", "set_level", "settings"]
