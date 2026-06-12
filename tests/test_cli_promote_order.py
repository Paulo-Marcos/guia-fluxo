"""Regression test for achado 2.2: cmd_promote ordem grava-antes-de-criar.

Anteriormente, se attach_worktree ou create_promoted_task falhassem, o
backlog ja havia sido gravado SEM o item. Agora o item so e removido do
backlog DEPOIS que a task foi construida com sucesso.

Este teste simula uma falha no worktree (passando uma branch invalida no
ambiente do sandbox sem .git) e confirma que o backlog continua intacto.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import REPO_ROOT

CORE_SRC = REPO_ROOT / "core" / "src"
CORE_LOCK = REPO_ROOT / "core" / "lock"


def _seed_sandbox(sandbox: Path) -> None:
    (sandbox / "core" / "src").mkdir(parents=True)
    (sandbox / "core" / "lock").mkdir(parents=True)
    for src in CORE_SRC.glob("*.py"):
        if not src.name.startswith("__"):
            shutil.copy2(src, sandbox / "core" / "src" / src.name)
    shutil.copy2(CORE_LOCK / "lock_api.py", sandbox / "core" / "lock" / "lock_api.py")


def _run(sandbox: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "core/src/guia.py", *args],
        cwd=sandbox,
        capture_output=True,
        text=True,
        encoding="utf-8",  # CLI emite UTF-8 (emoji markers); Windows default e cp1252.
    )


class PromoteOrderTests(unittest.TestCase):
    def test_promote_without_worktree_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed_sandbox(sandbox)
            self.assertEqual(_run(sandbox, "init", "--project-name", "t").returncode, 0)
            self.assertEqual(_run(sandbox, "backlog", "add", "Future").returncode, 0)
            # ADR-0011: backlog add cria D-001 (status=Backlog) em tasks.json.
            result = _run(sandbox, "promote", "D-001", "--kind", "feature")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            tasks = json.loads((sandbox / ".guia" / "tasks.json").read_text(encoding="utf-8"))
            backlog = json.loads((sandbox / ".guia" / "backlog.json").read_text(encoding="utf-8"))
            promoted = next((t for t in tasks["tasks"] if t["id"] == "D-001"), None)
            self.assertIsNotNone(promoted)
            self.assertEqual(promoted["status"], "Em desenvolvimento")  # saiu do Backlog
            self.assertEqual(backlog["items"], [])  # backlog.json legacy permanece vazio

    def test_promote_failure_keeps_demand_intact(self) -> None:
        """Sem .git no sandbox, --worktree falha em git_branch_exists.

        ADR-0011: o item de backlog vive em tasks.json (status=Backlog) e
        promote o muta in-place. Esperado: a demanda D-001 nunca se perde -
        fica preservada como Backlog (falha) ou ja promovida (sucesso).
        """
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed_sandbox(sandbox)
            self.assertEqual(_run(sandbox, "init", "--project-name", "t").returncode, 0)
            self.assertEqual(_run(sandbox, "backlog", "add", "Future").returncode, 0)
            result = _run(
                sandbox,
                "promote",
                "D-001",
                "--kind",
                "feature",
                "--worktree",
                "--branch",
                "guia-fluxo/test-branch",
            )
            # Pode passar OU falhar dependendo do git no sandbox.
            # O que NAO pode acontecer e: a demanda sumir de tasks.json.
            tasks = json.loads((sandbox / ".guia" / "tasks.json").read_text(encoding="utf-8"))
            demand = next((t for t in tasks["tasks"] if t["id"] == "D-001"), None)
            # invariante: a demanda continua registrada, em Backlog (preservada)
            # ou Em desenvolvimento (promovida). Nunca perdida.
            self.assertIsNotNone(demand, msg=result.stderr)
            self.assertIn(
                demand["status"],
                ("Backlog", "Em desenvolvimento"),
                msg=result.stderr,
            )


if __name__ == "__main__":
    unittest.main()
