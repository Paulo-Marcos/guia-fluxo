"""Deriva entre a configuracao de entrega e o GitHub (D-118, R2).

Compara os fatos da D-117 com o que o modo `pr` precisa para ser seguro.
Cada regra diz o risco concreto, nao so a diferenca. Fato que nao pode ser
lido (sem `gh`, sem remoto) nao gera deriva: o fato ja traz a nota. No modo
`direct` nao ha o que comparar.
"""

from __future__ import annotations

from typing import Any

from _constants import DELIVERY_MODE_PR


def _by_name(facts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {fact["name"]: fact for fact in facts}


def _protection_drift(protection: dict[str, Any], audit_context: str | None, aggregator: str | None) -> list[str]:
    drift: list[str] = []
    checks = protection.get("checks") or []
    if audit_context and audit_context not in checks:
        drift.append(
            f"a auditoria grava o status {audit_context!r}, mas a protecao nao o exige: "
            "o merge passa sem auditoria."
        )
    if aggregator and aggregator not in checks:
        drift.append(f"o agregador {aggregator!r} nao e check exigido: o merge passa com CI vermelho.")
    if not protection.get("strict"):
        drift.append(
            "strict desligado: PR desatualizado entra sem testar a combinacao com a main "
            "(conflito semantico)."
        )
    if not protection.get("enforceAdmins"):
        drift.append("enforce_admins desligado: o admin empurra direto na main, sem PR.")
    return drift


def _merge_drift(merge: dict[str, Any]) -> list[str]:
    drift: list[str] = []
    if "squash" not in (merge.get("methods") or []):
        drift.append("squash desligado: o modo pr integra por squash (um commit por demanda).")
    if merge.get("autoMerge"):
        drift.append("auto-merge ligado: um PR pode entrar por fora da fila e da auditoria do Guia.")
    return drift


def delivery_drift(facts: list[dict[str, Any]], config: dict[str, Any]) -> list[str]:
    delivery = config.get("delivery") or {}
    if delivery.get("mode") != DELIVERY_MODE_PR:
        return []
    by_name = _by_name(facts)
    drift: list[str] = []

    workflow = by_name.get("audit-workflow", {}).get("value") or {}
    workflow_context = workflow.get("statusContext")
    configured_context = (delivery.get("audit") or {}).get("statusContext")
    if configured_context and workflow_context and configured_context != workflow_context:
        drift.append(
            f"delivery.audit.statusContext = {configured_context!r}, mas o workflow de auditoria grava "
            f"{workflow_context!r}: o status gravado nunca e o exigido, e todo PR trava."
        )
    audit_context = configured_context or workflow_context

    protection_fact = by_name.get("protection", {})
    if protection_fact.get("value") is not None:
        aggregator = by_name.get("ci-aggregator", {}).get("value")
        drift += _protection_drift(protection_fact["value"], audit_context, aggregator)
    elif by_name.get("gh", {}).get("value") == "autenticado" and by_name.get("remote", {}).get("value"):
        drift.append("modo pr sem protecao na branch base: qualquer um empurra direto, sem PR nem CI.")

    merge = by_name.get("merge", {}).get("value")
    if merge is not None:
        drift += _merge_drift(merge)
    return drift


__all__ = ["delivery_drift"]
