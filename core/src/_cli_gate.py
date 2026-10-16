"""CLI handler: gate (D-182)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _changelog import work_root
from _constants import PROCESS_FILE
from _gate import describe_pass, gate_commands, passed_entry, record_pass, run_gate
from _state import read_json


def cmd_gate(args: argparse.Namespace) -> int:
    """Roda `delivery.gate.full` na arvore atual e grava o tree que passou."""
    commands = gate_commands(read_json(PROCESS_FILE, {}))
    if not commands:
        print("Guia Fluxo: sem delivery.gate.full - nada a rodar.", file=sys.stderr)
        return 0
    root = work_root(Path.cwd())
    entry = None if args.rerun else passed_entry(root, commands)
    if entry:
        print(f"{describe_pass(entry)}; --rerun roda de novo.")
        return 0
    failure = run_gate(root, commands)
    if failure:
        print(failure, file=sys.stderr)
        return 1
    if record_pass(root, commands):
        print("portao ok - tree gravado; o ship nao roda de novo enquanto o HEAD tiver este conteudo.")
    else:
        print("portao ok - arvore suja, tree NAO gravado (commite e rode de novo para o ship reaproveitar).")
    return 0


__all__ = ["cmd_gate"]
