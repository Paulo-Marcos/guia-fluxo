"""O modelo usado em cada demanda, ao lado do recomendado (D-154, epico E-010).

O chat e cada subagente registram o modelo com que trabalharam e para que
(`model <D-NNN> --who chat|subagent --model ... --purpose "..."`). A demanda
guarda `modelsUsed`, e cada registro leva o recomendado (da triagem, D-153; a
auditoria tem piso Opus). O resumo responde a pergunta do dono: o que foi feito
num modelo acima (ou abaixo) do adequado.
"""

from __future__ import annotations

from typing import Any

from _clock import now_iso

MODELS = ("haiku", "sonnet", "opus", "fable")
WHO = ("chat", "subagent")
AUDIT_FLOOR = "opus"
ABOVE, EQUAL, BELOW, UNKNOWN = "acima", "igual", "abaixo", "sem triagem"


def recommended_for(task: dict[str, Any], purpose: str) -> str | None:
    """O recomendado para este uso: a auditoria nunca abaixo de Opus; o resto, a triagem."""
    triage = task.get("triage") or {}
    if "audit" in purpose.lower() or "auditar" in purpose.lower():
        return triage.get("audit") or AUDIT_FLOOR
    return triage.get("model")


def compare(used: str, recommended: str | None) -> str:
    if recommended not in MODELS:
        return UNKNOWN
    delta = MODELS.index(used) - MODELS.index(recommended)
    return ABOVE if delta > 0 else BELOW if delta < 0 else EQUAL


def record(task: dict[str, Any], who: str, model: str, purpose: str, effort: str | None) -> dict[str, Any]:
    if who not in WHO:
        raise SystemExit(f"--who {who!r}: use {', '.join(WHO)}.")
    if model not in MODELS:
        raise SystemExit(f"--model {model!r}: use {', '.join(MODELS)}.")
    recommended = recommended_for(task, purpose)
    entry = {"who": who, "model": model, "effort": effort, "purpose": purpose, "recommended": recommended,
             "vs": compare(model, recommended), "at": now_iso()}
    task.setdefault("modelsUsed", []).append(entry)
    return entry


def summary(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """Contagem por comparacao e as demandas com uso acima do recomendado."""
    counts = {ABOVE: 0, EQUAL: 0, BELOW: 0, UNKNOWN: 0}
    above: list[dict[str, Any]] = []
    for task in tasks:
        for entry in task.get("modelsUsed") or []:
            counts[entry["vs"]] += 1
            if entry["vs"] == ABOVE:
                above.append({"task": task["id"], "who": entry["who"], "model": entry["model"],
                              "recommended": entry["recommended"], "purpose": entry["purpose"]})
    return {"counts": counts, "above": above}


__all__ = ["MODELS", "WHO", "compare", "record", "recommended_for", "summary"]
