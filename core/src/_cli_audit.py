"""CLI handler: audit (D-123)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from _audit import AUDIT_CHECKLIST, RESULT_APPROVED, audit_target, record_audit
from _audit_delta import MODE_FULL, delta_plan
from _auto_finish import findings_over_limit
from _autonomy import solo
from _cli_lifecycle import _plugin_templates_dir
from _conductor import announce_next
from _constants import PROCESS_FILE
from _skills import STAGE_AUDIT, announce_stage, record_stage, stage_skills
from _state import read_json
from _tasks import find_task_or_current, save_task


def _print_checklist() -> None:
    templates = _plugin_templates_dir()
    path = templates / AUDIT_CHECKLIST if templates else None
    if path is None or not path.is_file():
        print("Checklist embutido nao encontrado (templates/).", file=sys.stderr)
        return
    print(path.read_text(encoding="utf-8"))


def _print_delta(previous: dict[str, Any] | None, plan: dict[str, Any] | None) -> None:
    """D-140/D-207: head novo desde a ultima auditoria - o range-diff e o que conferir nele."""
    if not plan:
        return
    verdict = "aprovada" if plan["fromResult"] == RESULT_APPROVED else "reprovada"
    if plan["mode"] == MODE_FULL:
        print(f"Auditoria completa: o head mudou desde a {verdict} ({plan['from'][:12]}), mas {plan['reason']}.")
        if plan.get("range"):
            print(f"Para o relatorio, o que mudou: git range-diff {plan['range']}")
        return
    print(f"Auditoria de delta: o head mudou desde a {verdict} ({plan['from'][:12]}); "
          f"{plan['lines']} linhas em {len(plan['files'])} arquivo(s).")
    print(f"Audite so o que mudou: git range-diff {plan['range']}")
    findings = (previous or {}).get("findings") or []
    if findings:
        print("Confira cada achado anterior como fechado (ou ainda aberto, e repita-o no relatorio):")
        for finding in findings:
            print(f"  - {finding}")
    print("E confira se a correcao tocou o que ja estava ok.")


def _parse_findings(values: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        severity, _, number = value.partition("=")
        if not severity.strip() or not number.strip().isdigit():
            raise SystemExit(f"--finding {value!r}: use SEVERIDADE=N (ex.: BLOQUEANTE=0).")
        counts[severity.strip().upper()] = int(number)
    return counts


def cmd_audit(args: argparse.Namespace) -> int:
    """Mostra o que auditar; com --report, comenta no PR (e aprova com --approve)."""
    task = find_task_or_current(args.task_id)
    config = read_json(PROCESS_FILE, {})
    target = audit_target(config)
    skills, _disabled = stage_skills(STAGE_AUDIT, config)
    missing = set(args.skill_missing or [])
    use_checklist = not skills or set(skills) <= missing

    if not args.report:
        announce_stage(STAGE_AUDIT, config)
        print(f"{task['id']}: head {target['head']} (remoto {target['remoteHead'] or '-'}), patch-id {target['patchId'] or '-'}")
        _print_delta(task.get("audit"), delta_plan(target["root"], task.get("audit"), target, config))
        if use_checklist:
            print("Sem a skill de auditoria: audite pelo checklist embutido abaixo.\n")
            _print_checklist()
        return 0

    report = Path(args.report).read_text(encoding="utf-8")
    findings = _parse_findings(args.finding) if args.finding else None
    over = findings_over_limit(findings, config) if findings and args.approve and solo(config) else {}
    if over:
        # D-193 (ADR-0021): no solo o achado volta para o agente, nao para o dono.
        raise SystemExit(f"{task['id']}: perfil solo - achados abertos {over} acima do limite. "
                         "Corrija na branch, rode o ship e audite o head novo.")
    via = "checklist" if use_checklist else ", ".join(args.skill_ran or skills)
    audit = record_audit(task, target, report, args.approve, via, config)
    if findings is not None:
        # D-135: contagem de achados abertos por severidade, para a R7.
        audit["openFindings"] = findings
    record_stage(task, STAGE_AUDIT, config, args.skill_ran, args.skill_missing)
    save_task(task)
    verdict = "aprovada, marcador comentado" if args.approve else "registrada sem aprovacao (sem marcador)"
    print(f"{task['id']}: auditoria {verdict} no PR #{task['pr']['number']} - head {audit['auditedSha']}")
    announce_next(task, config)
    return 0


__all__ = ["cmd_audit"]
