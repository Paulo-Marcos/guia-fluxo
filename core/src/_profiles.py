"""Perfis de entrega (D-119, R2): propor pelos fatos, aplicar so com pedido.

Um perfil so preenche chaves que o motor ja usa - nada de configuracao que
nenhum codigo le. Aplicar nunca sobrescreve chave existente: o que o dono do
projeto configurou vence, e a saida lista o que foi mantido.
"""

from __future__ import annotations

import copy
from typing import Any

from _constants import COMMIT_FORMAT_GITMOJI, DELIVERY_MODE_DIRECT, DELIVERY_MODE_PR

PROFILE_SOLO_DIRECT = "solo-direct"
PROFILE_PR_BASIC = "pr-basic"
PROFILE_PR_AUDITED = "pr-audited"
PROFILES = (PROFILE_SOLO_DIRECT, PROFILE_PR_BASIC, PROFILE_PR_AUDITED)


def _value(facts: list[dict[str, Any]], name: str) -> Any:
    return next((fact.get("value") for fact in facts if fact["name"] == name), None)


def propose_profile(facts: list[dict[str, Any]]) -> tuple[str, list[str]]:
    """(perfil, motivos) a partir dos fatos da D-117."""
    if not _value(facts, "remote"):
        return PROFILE_SOLO_DIRECT, ["sem remoto GitHub: nao ha onde abrir PR"]
    audit = _value(facts, "audit-workflow")
    if audit:
        return PROFILE_PR_AUDITED, [f"workflow de auditoria em {audit['file']} grava o status {audit['statusContext']!r}"]
    protection = _value(facts, "protection") or {}
    aggregator = _value(facts, "ci-aggregator")
    if aggregator or protection.get("checks"):
        reason = f"agregador de CI {aggregator!r}" if aggregator else f"checks exigidos {protection['checks']}"
        return PROFILE_PR_BASIC, [f"{reason}, sem workflow de auditoria"]
    return PROFILE_SOLO_DIRECT, ["sem CI no PR e sem protecao na base"]


def profile_delivery(name: str, facts: list[dict[str, Any]]) -> dict[str, Any]:
    """Bloco `delivery` do perfil, so com chaves que o motor le."""
    if name == PROFILE_SOLO_DIRECT:
        return {"mode": DELIVERY_MODE_DIRECT}
    block: dict[str, Any] = {"mode": DELIVERY_MODE_PR, "commit": {"format": COMMIT_FORMAT_GITMOJI}}
    if name == PROFILE_PR_AUDITED:
        audit = _value(facts, "audit-workflow") or {}
        if audit.get("statusContext"):
            block["audit"] = {"statusContext": audit["statusContext"]}
    return block


def merge_missing(current: dict[str, Any], proposed: dict[str, Any], prefix: str = "delivery") -> tuple[dict[str, Any], list[str], list[str]]:
    """Acrescenta a `current` so as chaves ausentes de `proposed`.

    Devolve (resultado, chaves acrescentadas, chaves mantidas por ja existirem
    com outro valor).
    """
    result = copy.deepcopy(current)
    added: list[str] = []
    kept: list[str] = []
    for key, value in proposed.items():
        path = f"{prefix}.{key}"
        if key not in result:
            result[key] = copy.deepcopy(value)
            added.append(path)
        elif isinstance(value, dict) and isinstance(result[key], dict):
            result[key], sub_added, sub_kept = merge_missing(result[key], value, path)
            added += sub_added
            kept += sub_kept
        elif result[key] != value:
            kept.append(path)
    return result, added, kept


__all__ = [
    "PROFILES",
    "PROFILE_PR_AUDITED",
    "PROFILE_PR_BASIC",
    "PROFILE_SOLO_DIRECT",
    "merge_missing",
    "profile_delivery",
    "propose_profile",
]
