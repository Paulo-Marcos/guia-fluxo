"""Triagem de complexidade: o modelo e o esforco adequados a demanda (D-153, epico E-010).

O agente informa os sinais que enxerga lendo o pedido e o codigo; o motor aplica
uma regua fixa e explicavel e grava a recomendacao na demanda, com o porque -
consistente entre demandas e comparavel depois com o modelo de fato usado
(D-154). A regua:

    trivial   chore/docs/test, 1 area, sem risco, sem incerteza  -> haiku,  low
    normal    ate 2 areas, sem risco, sem incerteza                -> sonnet, medium
    complexa  3+ areas, ou qualquer risco, ou incerteza            -> opus,   high
    extrema   2+ riscos com incerteza, ou irreversivel com risco   -> fable (so sugestao com pergunta) ou opus max

A auditoria nunca roda abaixo de opus: quem confere tem de ser pelo menos tao
forte quanto quem escreveu.
"""

from __future__ import annotations

from typing import Any

from _clock import now_iso

TIER_TRIVIAL, TIER_NORMAL, TIER_COMPLEX, TIER_EXTREME = "trivial", "normal", "complexa", "extrema"
RISKS = ("auth", "migration", "concurrency", "security", "prod", "data")
LIGHT_KINDS = ("chore", "docs", "test")
MODELS_DEFAULT = {TIER_TRIVIAL: "haiku", TIER_NORMAL: "sonnet", TIER_COMPLEX: "opus", TIER_EXTREME: "opus"}
EFFORT = {TIER_TRIVIAL: "low", TIER_NORMAL: "medium", TIER_COMPLEX: "high", TIER_EXTREME: "max"}
AUDIT_FLOOR = "opus"
FABLE = "fable"
MODEL_NAMES = {"haiku": "Haiku 5.5", "sonnet": "Sonnet 5.5", "opus": "Opus 5.5", "fable": "Fable 5.1"}
_RANK = ("haiku", "sonnet", "opus", "fable")


def settings(config: dict[str, Any]) -> dict[str, Any]:
    """`models` do process.json: modelo por faixa e a politica do Fable (D-155)."""
    custom = config.get("models") or {}
    tiers = {**MODELS_DEFAULT, **(custom.get("tiers") or {})}
    enabled = custom.get("enabled", "on") not in (False, "off")
    return {"enabled": enabled, "tiers": tiers, "fable": custom.get("fable", "ask")}


def tier_of(kind: str, scope: int, risks: list[str], uncertain: bool, irreversible: bool) -> tuple[str, list[str]]:
    """(faixa, motivos) pela regua fixa."""
    why = [f"tipo {kind}", f"{scope} area(s)"]
    if risks:
        why.append("risco: " + ", ".join(risks))
    if uncertain:
        why.append("causa ou solucao incerta")
    if irreversible:
        why.append("dificil de desfazer")
    if (len(risks) >= 2 and uncertain) or (irreversible and risks):
        return TIER_EXTREME, why
    if scope >= 3 or risks or uncertain:
        return TIER_COMPLEX, why
    if kind in LIGHT_KINDS and scope <= 1:
        return TIER_TRIVIAL, why
    return TIER_NORMAL, why


def recommend(task: dict[str, Any], config: dict[str, Any], scope: int, risks: list[str],
              uncertain: bool, irreversible: bool) -> dict[str, Any]:
    """A recomendacao gravada na demanda (`triage`)."""
    unknown = [r for r in risks if r not in RISKS]
    if unknown:
        raise SystemExit(f"Risco desconhecido: {', '.join(unknown)}. Use: {', '.join(RISKS)}.")
    conf = settings(config)
    tier, why = tier_of(task.get("kind", ""), scope, risks, uncertain, irreversible)
    model = conf["tiers"][tier]
    suggestion = None
    if tier == TIER_EXTREME and conf["fable"] != "never":
        # Fable custa ~2,5x o Opus e faz turnos longos: sugere, nao decide (D-155).
        suggestion = {"model": FABLE, "ask": conf["fable"] == "ask",
                      "why": "o mais capaz, para raciocinio exigente e trabalho longo; custa mais"}
    return {
        "tier": tier, "model": model, "effort": EFFORT[tier], "why": why, "suggestion": suggestion,
        "audit": max(model, AUDIT_FLOOR, key=_RANK.index), "at": now_iso(),
        "signals": {"scope": scope, "risks": risks, "uncertain": uncertain, "irreversible": irreversible},
    }


def describe(triage: dict[str, Any]) -> str:
    line = (f"{triage['tier']}: {MODEL_NAMES[triage['model']]}, esforco {triage['effort']} "
            f"({'; '.join(triage['why'])}); auditoria: {MODEL_NAMES[triage['audit']]}")
    sug = triage.get("suggestion")
    if sug:
        line += f"; sugestao: {MODEL_NAMES[sug['model']]}" + (" (pergunte ao dono)" if sug["ask"] else "")
    return line


__all__ = ["AUDIT_FLOOR", "MODEL_NAMES", "RISKS", "describe", "recommend", "settings", "tier_of"]
