"""CLI handler: configure (D-143, epico E-008)."""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from typing import Any

from _configure import STEPS, apply_answers, build_plan, outside_notes, save
from _configure_tty import run as run_terminal
from _constants import ROOT, PROCESS_FILE
from _delivery_facts import collect_facts
from _state import read_json

WIDTH = 88


def _answers(pairs: list[str]) -> dict[str, str]:
    answers = {}
    for pair in pairs:
        step_id, sep, value = pair.partition("=")
        if not sep:
            raise SystemExit(f"--set {pair!r}: use ETAPA=VALOR (ex.: mode=pr).")
        answers[step_id.strip()] = value
    return answers


def _show(value: Any) -> str:
    if value is None:
        return "(ausente)"
    return json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value


def _print_step(index: int, item: dict[str, Any]) -> None:
    print(f"\n[{index}/{len(STEPS)}] {item['section']} - {item['title']}  ({item['status']})")
    for line in textwrap.wrap(item["explain"], WIDTH - 2):
        print(f"  {line}")
    for line in item["seen"]:
        print(f"  Visto no projeto: {line}")
    for option in item["options"]:
        mark = "*" if option["value"] == item["recommended"] else " "
        why = f" ({option['why']})" if option["why"] else ""
        print(f"   {mark} {_show(option['value'])}: {option['label']}{why}")
    print(f"  Atual: {_show(item['current'])}  (padrao do motor: {_show(item['default'])})")
    print(f"  Recomendado: {_show(item['recommended'])} - {item['recommendedWhy']}")
    if item["note"]:
        print(f"  Nota: {item['note']}")


def print_plan(plan: list[dict[str, Any]]) -> None:
    for index, item in enumerate(plan, start=1):
        if item["applies"]:
            _print_step(index, item)
        else:
            print(f"\n[{index}/{len(STEPS)}] {item['section']} - {item['title']}  (nao se aplica com as escolhas atuais)")
    print("\nPara escolher: guia configure --set ETAPA=VALOR [--set ...] (simula); com --yes grava.")
    print("Valores: `padrao` volta ao padrao do motor; listas separadas por virgula; `nenhuma` = lista vazia.")


SIMULATION_HINT = "Simulacao: nada gravado. Repita com --yes para gravar."


def print_changes(changes: list[dict[str, Any]], notes: list[str], written: bool, backup: Any,
                  hint: str | None = SIMULATION_HINT) -> None:
    if not changes:
        print("Nada muda: as escolhas ja sao as do process.json.")
    for change in changes:
        print(f"  {change['path']}: {_show(change['before'])} -> {_show(change['after'])}")
    if changes and written:
        print(f"Gravado em {PROCESS_FILE}" + (f" (anterior em {backup})" if backup else "") + ".")
    elif changes and hint:
        print(hint)
    for note in notes:
        print(f"Fora do process.json (aplique voce): {note}")


def _print_summary(changes: list[dict[str, Any]], notes: list[str], written: bool, backup: Any) -> None:
    print_changes(changes, notes, written, backup, hint=None)


def cmd_configure(args: argparse.Namespace) -> int:
    """Plano das etapas (o que decidir, o que o Guia viu, a recomendacao) e a gravacao."""
    config = read_json(PROCESS_FILE, {})
    facts = collect_facts()
    asked = not (args.plan or args.set or args.json)
    if args.interactive or (asked and sys.stdin.isatty()):
        # D-144: o painel do terminal - uma etapa por vez, sobre o mesmo plano.
        return run_terminal(config, facts, ROOT, _print_step, _print_summary, only_pending=args.pendentes)
    updated, changes = apply_answers(config, _answers(args.set))
    if args.set and not args.plan:
        backup = save(updated) if args.yes and changes else None
        notes = outside_notes(updated, facts)
        if args.json:
            print(json.dumps({"changes": changes, "written": bool(args.yes and changes), "notes": notes,
                              "backup": str(backup) if backup else None}, ensure_ascii=False, indent=2))
        else:
            print_changes(changes, notes, bool(args.yes), backup)
        return 0
    # O plano reflete as respostas ja dadas (--set): as etapas que dependem de
    # outras (ex.: so no modo pr) aparecem ou somem conforme a escolha.
    plan = build_plan(updated, facts, ROOT)
    if args.json:
        print(json.dumps({"steps": plan, "pending": changes}, ensure_ascii=False, indent=2))
    else:
        print_plan(plan)
    return 0


__all__ = ["cmd_configure", "print_changes", "print_plan"]
