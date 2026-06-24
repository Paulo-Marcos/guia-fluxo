"""D-049: tests for epic→stories hierarchy.

Cobre: criacao de Epic (E-NNN com numeracao propria); --under cria story;
recusa parent inexistente; recusa parent que nao e epic (sem aninhamento);
status do Epic mostra arvore agregada; finish do Epic recusa enquanto ha
filhos abertos; cancel do Epic NAO mexe nos filhos.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import REPO_ROOT

CORE_SRC = REPO_ROOT / "core" / "src"
CORE_LOCK = REPO_ROOT / "core" / "lock"


def _seed(sandbox: Path) -> None:
    (sandbox / "core" / "src").mkdir(parents=True)
    (sandbox / "core" / "lock").mkdir(parents=True)
    for src in CORE_SRC.glob("*.py"):
        if not src.name.startswith("__"):
            shutil.copy2(src, sandbox / "core" / "src" / src.name)
    shutil.copy2(CORE_LOCK / "lock_api.py", sandbox / "core" / "lock" / "lock_api.py")


def _run(sandbox: Path, *args: str) -> subprocess.CompletedProcess[str]:
    # D-080: finish exige a env de autorizacao humana; a suite roda autorizada.
    env = {**os.environ, "GUIA_HUMAN_FINISH": "1"}
    return subprocess.run(
        [sys.executable, "core/src/guia.py", *args],
        cwd=sandbox,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )


def _show(sandbox: Path, task_id: str) -> dict:
    result = _run(sandbox, "tasks", "show", task_id, "--json")
    return json.loads(result.stdout)


class EpicCreationTests(unittest.TestCase):
    def test_epic_gets_e_prefix_and_own_numbering(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            # Cria varias tasks D-NNN primeiro: epic comeca em E-001 independente.
            _run(sandbox, "feature", "Tarefa A")
            _run(sandbox, "feature", "Tarefa B")
            result = _run(sandbox, "epic", "Epico grande")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("E-001 created", result.stdout)
            epic = _show(sandbox, "E-001")
            self.assertEqual(epic["kind"], "epic")
            self.assertEqual(epic["status"], "Em desenvolvimento")
            self.assertNotIn("parentId", epic)

    def test_under_creates_child_with_parent_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _run(sandbox, "epic", "Epico X")
            result = _run(sandbox, "feature", "Sub Y", "--under", "E-001")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            child = _show(sandbox, "D-001")
            self.assertEqual(child["parentId"], "E-001")

    def test_under_recused_when_parent_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            result = _run(sandbox, "feature", "Orfa", "--under", "E-999")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("nao existe", result.stderr)

    def test_under_recused_when_parent_is_not_epic(self) -> None:
        """Sem aninhamento: --under D-001 (feature) deve falhar."""
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _run(sandbox, "feature", "Mae nao-epic")
            result = _run(sandbox, "feature", "Sub", "--under", "D-001")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Sem epics aninhados", result.stderr)


class EpicStatusTreeTests(unittest.TestCase):
    def test_status_shows_aggregated_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _run(sandbox, "epic", "Epico")
            _run(sandbox, "feature", "Filho 1", "--under", "E-001")
            _run(sandbox, "bug", "Filho 2", "--under", "E-001")
            result = _run(sandbox, "status", "E-001")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("Progresso: 0/2", result.stdout)
            self.assertIn("D-001", result.stdout)
            self.assertIn("D-002", result.stdout)
            self.assertIn("Bloqueio", result.stdout)

    def test_status_empty_epic_shows_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _run(sandbox, "epic", "Epico solo")
            result = _run(sandbox, "status", "E-001")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("sem filhos ainda", result.stdout)


class EpicFinishGateTests(unittest.TestCase):
    def test_finish_recused_with_open_children(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _run(sandbox, "epic", "Epico")
            _run(sandbox, "feature", "Filho aberto", "--under", "E-001")
            result = _run(sandbox, "finish", "E-001", "--no-commit", "--docs-skip", "x")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("filho(s) abertos", result.stderr)

    def test_finish_allowed_when_all_children_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _run(sandbox, "epic", "Epico")
            _run(sandbox, "feature", "Filho", "--under", "E-001")
            _run(sandbox, "ready", "D-001", "--summary", "ok")
            _run(sandbox, "finish", "D-001", "--no-commit", "--docs-skip", "x")
            # Agora finish do epic deve passar.
            result = _run(sandbox, "finish", "E-001", "--no-commit", "--docs-skip", "x")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(_show(sandbox, "E-001")["status"], "Validada")

    def test_cancelled_child_satisfies_finish(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _run(sandbox, "epic", "Epico")
            _run(sandbox, "feature", "Filho descartado", "--under", "E-001")
            _run(sandbox, "cancel", "D-001", "--reason", "fora de escopo")
            result = _run(sandbox, "finish", "E-001", "--no-commit", "--docs-skip", "x")
            self.assertEqual(result.returncode, 0, msg=result.stderr)


class CancelDoesNotCascadeTests(unittest.TestCase):
    def test_cancel_epic_leaves_children_intact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _run(sandbox, "epic", "Epico")
            _run(sandbox, "feature", "Filho 1", "--under", "E-001")
            _run(sandbox, "feature", "Filho 2", "--under", "E-001")
            result = _run(sandbox, "cancel", "E-001", "--reason", "vamos parar")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(_show(sandbox, "E-001")["status"], "Cancelada")
            # Filhos seguem intactos.
            self.assertEqual(_show(sandbox, "D-001")["status"], "Em desenvolvimento")
            self.assertEqual(_show(sandbox, "D-002")["status"], "Em desenvolvimento")


if __name__ == "__main__":
    unittest.main()
