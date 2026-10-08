"""CLI handler: profile (D-119)."""

from __future__ import annotations

import argparse
import json

from _constants import PROCESS_FILE
from _delivery_facts import collect_facts
from _profiles import merge_missing, profile_delivery, propose_profile
from _state import read_json, write_json


def cmd_profile(args: argparse.Namespace) -> int:
    """Propoe o perfil de entrega pelos fatos; com --apply, grava o bloco.

    `--apply` so acrescenta chaves ausentes em `delivery` (nunca sobrescreve)
    e lista as que manteve. Sem `--apply`, nada e gravado.
    """
    facts = collect_facts()
    proposed, reasons = propose_profile(facts)
    chosen = args.name or proposed
    block = profile_delivery(chosen, facts)
    added: list[str] = []
    kept: list[str] = []
    if args.apply:
        process = read_json(PROCESS_FILE, {})
        process["delivery"], added, kept = merge_missing(process.get("delivery") or {}, block)
        write_json(PROCESS_FILE, process)
    if args.json:
        print(json.dumps({
            "profile": chosen,
            "proposed": proposed,
            "reasons": reasons,
            "delivery": block,
            "applied": bool(args.apply),
            "added": added,
            "kept": kept,
        }, ensure_ascii=False, indent=2))
        return 0
    print(f"Perfil proposto: {proposed}")
    for reason in reasons:
        print(f"  - {reason}")
    if chosen != proposed:
        print(f"Perfil escolhido: {chosen}")
    print("Bloco delivery do perfil:")
    print(json.dumps(block, ensure_ascii=False, indent=2))
    if not args.apply:
        print("Nada gravado. Para aplicar: guia profile --apply [--name <perfil>]")
        return 0
    for path in added:
        print(f"  + {path}")
    for path in kept:
        print(f"  = {path} (ja configurado com outro valor - mantido)")
    if not added and not kept:
        print("  (nada a acrescentar: o process.json ja tem o perfil)")
    return 0


__all__ = ["cmd_profile"]
