"""Fechar a demanda sem precisar pedir (D-135, R7).

No nivel `pilot`, depois de o executor integrar o PR, o motor fecha a demanda
sozinho quando TODAS as condicoes de `autonomy.autoFinish` valem - e registra
cada uma com a evidencia (`finish.mode = "auto"`). Uma condicao sem evidencia
conta como nao atendida: na duvida, quem fecha e o dono.

O nivel `pilot` so sobe pelo usuario (D-133), entao o fechamento automatico e
a autorizacao explicita que a D-098 exige, dada antes, por demanda.

Fora do pilot vale o empurrao: demanda `Integrada` ha mais de
`remindAfterDays` dias aparece no `status` com a pergunta "fechar?".
"""

from __future__ import annotations

import fnmatch
from datetime import datetime, timezone
from typing import Any

from _autonomy import effective_level
from _clock import now_iso
from _constants import ROOT, STATUS_INTEGRATED, STATUS_VALIDATED
from _features_md import upsert_features_entry
from _git_ops import git_output
from _reports import write_report
from _tasks import list_tasks, save_task

AUTO_FINISH_DEFAULT: dict[str, Any] = {
    # `feature` fica fora: capacidade nova pede uso real.
    "kinds": ["chore", "test", "docs", "refactor", "bug"],
    "bugRequiresRegressionTest": True,
    "requireMainGreen": True,
    "maxOpenFindings": {"BLOQUEANTE": 0, "CORRIGIR": 0},
    "blockIfUiChanged": True,
    "uiPaths": ["frontend/src/**", "**/*.css", "**/*.html", "**/*.tsx", "**/*.jsx", "**/*.vue", "**/*.svelte"],
    "testPaths": ["tests/**", "test/**", "**/tests/**", "**/test_*.py", "**/*_test.py", "**/*.test.*", "**/*.spec.*"],
    "blockIfAlwaysHuman": True,
    "remindAfterDays": 3,
}


def settings(config: dict[str, Any]) -> dict[str, Any]:
    custom = (config.get("autonomy") or {}).get("autoFinish") or {}
    return {**AUTO_FINISH_DEFAULT, **custom}


def _matching(paths: list[str], patterns: list[str]) -> list[str]:
    def hit(path: str, pattern: str) -> bool:
        return fnmatch.fnmatch(path, pattern) or (pattern.startswith("**/") and fnmatch.fnmatch(path, pattern[3:]))

    return sorted({p for p in paths for pat in patterns if hit(p, pat)})


def squash_paths(sha: str | None) -> list[str] | None:
    """Arquivos do commit do squash, pelo git (None = nao deu para conferir)."""
    if not sha:
        return None
    names = git_output(ROOT, "diff", "--name-only", f"{sha}^", sha)
    return None if names is None else [line for line in names.splitlines() if line.strip()]


def evaluate(task: dict[str, Any], item: dict[str, Any], config: dict[str, Any],
             main_ci: str | None, paths: list[str] | None) -> list[dict[str, Any]]:
    """Cada condicao da R7 com o resultado e a evidencia."""
    conf = settings(config)
    kind = task.get("kind")
    checks: list[dict[str, Any]] = []

    def check(name: str, ok: bool, evidence: str) -> None:
        checks.append({"check": name, "ok": ok, "evidence": evidence})

    level = effective_level(task, config)
    check("nivel pilot", level == "pilot", f"nivel efetivo {level}")
    check("tipo permitido", kind in conf["kinds"], f"{kind} em {conf['kinds']}")
    if conf["requireMainGreen"]:
        check("main verde", main_ci == "pass", f"CI da main no squash: {main_ci or 'nao acompanhado'}")
    if kind == "bug" and conf["bugRequiresRegressionTest"]:
        tests = _matching(paths or [], conf["testPaths"])
        check("teste de regressao", bool(tests), ", ".join(tests) or "nenhum teste no squash")
    if conf["blockIfUiChanged"]:
        ui = _matching(paths or [], conf["uiPaths"])
        check("sem mudanca de tela", paths is not None and not ui,
              "caminhos do squash nao conferidos" if paths is None else (", ".join(ui) or "nenhum caminho de tela"))
    findings = (task.get("audit") or {}).get("openFindings")
    if findings is None:
        check("achados da auditoria", False, "auditoria sem contagem de achados (audit --finding SEV=N)")
    else:
        over = {sev: findings.get(sev, 0) for sev, limit in conf["maxOpenFindings"].items() if findings.get(sev, 0) > limit}
        check("achados da auditoria", not over, f"abertos {findings}, limite {conf['maxOpenFindings']}")
    if conf["blockIfAlwaysHuman"]:
        reason = item.get("humanReason")
        check("fora do alwaysHuman", not reason, reason or "nada em alwaysHuman")
    return checks


def auto_finish(task: dict[str, Any], checks: list[dict[str, Any]], config: dict[str, Any]) -> None:
    """Fecha como o `finish` no modo pr (sem commit), com o porque registrado."""
    task["status"] = (config.get("finish") or {}).get("status", STATUS_VALIDATED)
    task["finishedAt"] = now_iso()
    task["finish"] = {"mode": "auto", "at": task["finishedAt"], "checks": checks}
    task.setdefault("summary", []).append(
        "Fechada automaticamente no pilot (R7): " + "; ".join(f"{c['check']} ({c['evidence']})" for c in checks)
    )
    save_task(task)
    upsert_features_entry(task)
    write_report(task, "finish")


def try_auto_finish(task: dict[str, Any], item: dict[str, Any], config: dict[str, Any],
                    main_ci: str | None, sha: str | None) -> list[dict[str, Any]] | None:
    """Depois do merge: no pilot avalia a R7; devolve as checagens (None fora do pilot)."""
    if effective_level(task, config) != "pilot":
        return None
    checks = evaluate(task, item, config, main_ci, squash_paths(sha))
    if all(c["ok"] for c in checks):
        auto_finish(task, checks, config)
    return checks


def _age_days(stamp: str | None, now: datetime) -> float | None:
    try:
        moment = datetime.fromisoformat((stamp or "").replace("Z", "+00:00"))
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return (now - moment).total_seconds() / 86400


def stale_integrated(config: dict[str, Any], now: datetime | None = None) -> list[tuple[dict[str, Any], int]]:
    """Demandas `Integrada` ha mais de `remindAfterDays` dias (o empurrao da R7)."""
    limit = float(settings(config)["remindAfterDays"])
    now = now or datetime.now(timezone.utc)
    stale = []
    for task in list_tasks(status=STATUS_INTEGRATED):
        age = _age_days((task.get("pr") or {}).get("mergedAt"), now)
        if age is not None and age > limit:
            stale.append((task, int(age)))
    return stale


__all__ = ["AUTO_FINISH_DEFAULT", "auto_finish", "evaluate", "settings", "squash_paths", "stale_integrated", "try_auto_finish"]
