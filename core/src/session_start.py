"""Hook SessionStart do plugin: o relatorio de uma linha da faxina (D-202).

Entrada fina de proposito: o `guia.py` importa todos os verbos (~7 s numa
maquina fria), e o inicio de sessao espera o hook terminar. Aqui so a faxina
e carregada. Mudo fora de projeto Guia e quando nao ha o que limpar; nunca
falha - um hook com erro atrapalharia toda sessao, em qualquer projeto.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main() -> int:
    try:
        from _constants import GUIA_DIR

        if not GUIA_DIR.is_dir():
            return 0
        from _cleanup import scan, session_line

        line = session_line(scan(quick=True))
    except Exception:  # noqa: BLE001 - nunca quebra a sessao
        return 0
    if line:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
