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

import fnmatch
import re
from typing import Any

from _clock import now_iso

LEVELS = ("manual", "pr", "queue", "pilot")
LEVEL_DEFAULT = "manual"
CEILING_DEFAULT = "pilot"
BY_USER = "user"
BY_AGENT = "agent"
# D-134 (R6): caminhos que sempre param no humano, qualquer que seja o nivel.
ALWAYS_HUMAN_DEFAULT = (
    ".github/**",
    "**/migrations/**",
    ".guia/locks/**",
    "**/requirements*.txt",
    "**/package-lock.json",
)
_UNLOCK_RE = re.compile(r"\[unlock:([a-z0-9_\-]+)\]", re.IGNORECASE)


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


def _matches(path: str, pattern: str) -> bool:
    # `**/x/**` tambem casa `x/...` na raiz (o fnmatch exigiria um prefixo).
    return fnmatch.fnmatch(path, pattern) or (
        pattern.startswith("**/") and fnmatch.fnmatch(path, pattern[3:])
    )


def human_reasons(changed_paths: list[str] | None, merge_message: str, config: dict[str, Any]) -> list[str]:
    """Por que o merge precisa do dono, apesar do nivel (vazio = pode ir sozinho).

    `changed_paths` vem do git (diff da branch do PR contra a base), nunca da
    lista declarada pelo agente; None = nao foi possivel conferir, e o dono
    decide.
    """
    autonomy = config.get("autonomy") or {}
    patterns = autonomy.get("alwaysHuman") or list(ALWAYS_HUMAN_DEFAULT)
    locks = autonomy.get("alwaysHumanLocks", "*")
    reasons: list[str] = []
    if changed_paths is None:
        reasons.append("caminhos do PR nao conferidos pelo git")
    else:
        touched = sorted({p for p in changed_paths for pat in patterns if _matches(p, pat)})
        if touched:
            reasons.append("toca caminho alwaysHuman: " + ", ".join(touched))
    marked = sorted({m.lower() for m in _UNLOCK_RE.findall(merge_message or "")})
    held = [lock for lock in marked if locks == "*" or lock in (locks or [])]
    if held:
        reasons.append("desbloqueia trava: " + ", ".join(held))
    return reasons


def implicit_approval(task: dict[str, Any], config: dict[str, Any], reasons: list[str]) -> dict[str, Any] | None:
    """Nivel >= queue e nada em alwaysHuman: aprovacao pela autonomia."""
    level = effective_level(task, config)
    if rank(level) < rank("queue") or reasons:
        return None
    return {"by": "autonomy", "level": level, "at": now_iso()}


__all__ = [
    "ALWAYS_HUMAN_DEFAULT",
    "BY_AGENT",
    "BY_USER",
    "LEVELS",
    "effective_level",
    "human_reasons",
    "implicit_approval",
    "rank",
    "set_level",
    "settings",
]
