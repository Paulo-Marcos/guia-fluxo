"""CLI handler: audit (D-123)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _audit import AUDIT_CHECKLIST, audit_target, delta_range, record_audit
from _cli_lifecycle import _plugin_templates_dir
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
        delta = delta_range(target["root"], task.get("audit"), target)
        if delta:
            # D-140 (R8): o PR mudou desde a auditoria aprovada - audite so o delta.
            print(f"Auditoria de delta: o head mudou desde a aprovada ({task['audit']['auditedSha'][:12]}).")
            print(f"Audite so o que mudou: git range-diff {delta}")
        if use_checklist:
            print("Sem a skill de auditoria: audite pelo checklist embutido abaixo.\n")
            _print_checklist()
        return 0

    report = Path(args.report).read_text(encoding="utf-8")
    via = "checklist" if use_checklist else ", ".join(args.skill_ran or skills)
    audit = record_audit(task, target, report, args.approve, via)
    if args.finding:
        # D-135: contagem de achados abertos por severidade, para a R7.
        audit["openFindings"] = _parse_findings(args.finding)
    record_stage(task, STAGE_AUDIT, config, args.skill_ran, args.skill_missing)
    save_task(task)
    verdict = "aprovada, marcador comentado" if args.approve else "registrada sem aprovacao (sem marcador)"
    print(f"{task['id']}: auditoria {verdict} no PR #{task['pr']['number']} - head {audit['auditedSha']}")
    return 0


__all__ = ["cmd_audit"]
