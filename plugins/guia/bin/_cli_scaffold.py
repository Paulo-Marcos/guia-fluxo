"""CLI handler: scaffold (D-120)."""

from __future__ import annotations

import argparse
import sys

from _cli_lifecycle import _plugin_templates_dir
from _scaffold import scaffold


def cmd_scaffold(args: argparse.Namespace) -> int:
    """Gera um andaime de entrega a partir dos modelos do Guia."""
    templates = _plugin_templates_dir()
    if templates is None:
        print("Modelos do Guia nao encontrados (templates/).", file=sys.stderr)
        return 1
    code, text = scaffold(args.target, templates)
    print(text, file=sys.stdout if code == 0 else sys.stderr)
    return code


__all__ = ["cmd_scaffold"]
