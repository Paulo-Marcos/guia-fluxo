"""CLI handler: deps - os PRs do Dependabot (D-129)."""

from __future__ import annotations

import argparse
import json

from _dependabot import create_lote, inventory, open_lote


def cmd_deps(args: argparse.Namespace) -> int:
    inv = inventory()
    lote = create_lote(inv) if args.now else None
    if args.json:
        print(json.dumps({**inv, "lote": lote["id"] if lote else None}, ensure_ascii=False, indent=2))
        return 0
    print(f"PRs do Dependabot: {len(inv['bumps'])} bump(s), {len(inv['others'])} outro(s).")
    for bump in inv["bumps"]:
        flag = " [SEGURANCA]" if bump["security"] else ""
        print(f"  bump #{bump['number']}{flag}: {bump['title']}")
    for other in inv["others"]:
        print(f"  nao e bump #{other['number']}: {other['title']} - {other['reason']} (vai para a pr-audit)")
    existing = open_lote()
    if lote:
        print(f"Lote criado: {lote['id']}. Rode a skill pr-bump num chat.")
    elif existing:
        print(f"Lote aberto: {existing['id']} ({existing.get('status')}).")
    elif inv["bumps"]:
        print("Para criar o lote agora: guia deps --now (o executor cria sozinho com a fila vazia).")
    return 0


__all__ = ["cmd_deps"]
