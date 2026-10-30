"""Lugar fixo dos artefatos de agente: `.guia/tmp/<D-NNN>/` (D-202).

Relatorio de auditoria, log de portao, mensagem de commit, patch: sem um
lugar anunciado, cada agente escrevia onde estava - e a pasta pai dos
projetos (C:/DEV) juntou 75 arquivos soltos. A pasta fica na arvore
principal (o ROOT do estado, D-109), entao o mesmo caminho vale de dentro de
qualquer worktree, e um `.gitignore` com `*` a mantem fora do git em
qualquer projeto, mesmo sem regra no `.gitignore` dele.
"""

from __future__ import annotations

from pathlib import Path

from _constants import GUIA_DIR

ARTIFACTS_ROOT = GUIA_DIR / "tmp"


def artifacts_dir(task_id: str) -> Path:
    """Cria (se preciso) e devolve a pasta de artefatos da demanda."""
    folder = ARTIFACTS_ROOT / task_id
    folder.mkdir(parents=True, exist_ok=True)
    ignore = ARTIFACTS_ROOT / ".gitignore"
    if not ignore.exists():
        ignore.write_text("*\n", encoding="utf-8")
    return folder.resolve()


__all__ = ["ARTIFACTS_ROOT", "artifacts_dir"]
