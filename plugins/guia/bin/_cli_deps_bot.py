"""CLI handler: deps - os PRs do Dependabot (D-129, D-149)."""

from __future__ import annotations

import argparse
import json
from typing import Any

from _autonomy import effective_level
from _constants import PROCESS_FILE
from _dependabot import create_lote, inventory, open_lote
from _skills import STAGE_DEPS, announce_stage, stage_skills
from _state import read_json


def _lote_facts(lote: dict[str, Any] | None, config: dict[str, Any]) -> dict[str, Any]:
    """O que o roteiro do `/guia:deps --now` precisa saber do lote aberto (D-149)."""
    if not lote:
        return {"openLote": None, "level": None, "skills": []}
    skills, disabled = stage_skills(STAGE_DEPS, config)
    return {"openLote": lote["id"], "status": lote.get("status"), "level": effective_level(lote, config),
            "skills": [] if disabled else skills, "security": (lote.get("dependabot") or {}).get("security", False)}


def cmd_deps(args: argparse.Namespace) -> int:
    config = read_json(PROCESS_FILE, {})
    inv = inventory()
    lote = create_lote(inv, config) if args.now else None
    facts = _lote_facts(lote or open_lote(), config)
    if args.json:
        print(json.dumps({**inv, "lote": lote["id"] if lote else None, **facts}, ensure_ascii=False, indent=2))
        return 0
    print(f"PRs do Dependabot: {len(inv['bumps'])} bump(s), {len(inv['others'])} outro(s).")
    for bump in inv["bumps"]:
        flag = " [SEGURANCA]" if bump["security"] else ""
        print(f"  bump #{bump['number']}{flag}: {bump['title']}")
    for other in inv["others"]:
        print(f"  nao e bump #{other['number']}: {other['title']} - {other['reason']} (vai para a pr-audit)")
    if facts["openLote"]:
        verb = "criado" if lote else "aberto"
        print(f"Lote {verb}: {facts['openLote']} (nivel {facts['level']}, skill: {', '.join(facts['skills']) or 'nenhuma'}).")
        announce_stage(STAGE_DEPS, config)
    elif inv["bumps"]:
        print("Para criar o lote agora: guia deps --now (o executor cria sozinho com a fila vazia).")
    return 0


__all__ = ["cmd_deps"]
