"""CLI handler: cleanup - faxina da pasta pai do projeto (D-202)."""

from __future__ import annotations

import argparse
import json

from _cleanup import remove, render, scan
from _constants import GUIA_DIR


def cmd_cleanup(args: argparse.Namespace) -> int:
    """Lista worktrees inativas e arquivos soltos; remove so o que vier em `--remove`.

    `--session-start` e o mesmo relatorio de uma linha do hook SessionStart
    (`session_start.py`, a entrada fina que o hook chama).
    """
    if args.session_start:
        from session_start import main as session_start

        return session_start()
    if not GUIA_DIR.is_dir():
        raise SystemExit("Sem .guia/ aqui: rode a faxina da raiz de um projeto Guia.")
    if args.remove:
        for path in remove(args.remove):
            print(f"Removido: {path}")
        return 0
    report = scan()
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else render(report))
    return 0


__all__ = ["cmd_cleanup"]
