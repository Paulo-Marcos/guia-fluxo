"""D-067: tests for the dependency-between-demands feature.

Cobre: declaracao via --depends-on no feature/bug/chore; subcomando
`depends add/remove/list`; bloqueio de start/promote enquanto a dep
estiver aberta; deteccao de ciclo; auto-dep; id inexistente.
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


def _seed(sandbox: Path) -> None:
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
        encoding="utf-8",
    )


def _task_status(sandbox: Path, task_id: str) -> str:
    result = _run(sandbox, "tasks", "show", task_id, "--json")
    return json.loads(result.stdout).get("status", "?")


def _depends_on(sandbox: Path, task_id: str) -> list[str]:
    result = _run(sandbox, "tasks", "show", task_id, "--json")
    return json.loads(result.stdout).get("dependsOn", [])


class DeclareOnCreateTests(unittest.TestCase):
    def test_feature_accepts_multiple_depends_on(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _run(sandbox, "backlog", "add", "Dep A")
            _run(sandbox, "backlog", "add", "Dep B")
            result = _run(
                sandbox, "feature", "Dependente",
                "--depends-on", "D-001", "--depends-on", "D-002",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(_depends_on(sandbox, "D-003"), ["D-001", "D-002"])

    def test_depends_on_dedups_preserving_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _run(sandbox, "backlog", "add", "A")
            _run(
                sandbox, "feature", "B",
                "--depends-on", "D-001", "--depends-on", "D-001",
            )
            self.assertEqual(_depends_on(sandbox, "D-002"), ["D-001"])


class StartBlockingTests(unittest.TestCase):
    def test_start_recused_when_dep_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            # D-001: dep em desenvolvimento (NAO satisfaz)
            _run(sandbox, "feature", "Dep aberta")
            # D-002: dependente, parqueada no backlog
            _run(
                sandbox, "feature", "Dependente",
                "--status", "backlog", "--depends-on", "D-001",
            )
            result = _run(sandbox, "start", "D-002")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("dependencia(s) abertas", result.stderr)
            self.assertIn("D-001", result.stderr)
            # Continua em Backlog (nao avancou).
            self.assertEqual(_task_status(sandbox, "D-002"), "Backlog")

    def test_start_allowed_after_dep_finished(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _run(sandbox, "feature", "Dep")
            _run(
                sandbox, "feature", "Dependente",
                "--status", "backlog", "--depends-on", "D-001",
            )
            # Termina a dep (ready -> finish).
            _run(sandbox, "ready", "D-001", "--summary", "ok")
            _run(sandbox, "finish", "D-001", "--no-commit", "--docs-skip", "test")
            # Agora start deve funcionar.
            result = _run(sandbox, "start", "D-002")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(_task_status(sandbox, "D-002"), "Em desenvolvimento")

    def test_cancelled_dep_satisfies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _run(sandbox, "feature", "Dep")
            _run(
                sandbox, "feature", "Dependente",
                "--status", "backlog", "--depends-on", "D-001",
            )
            _run(sandbox, "cancel", "D-001", "--reason", "fora de escopo")
            result = _run(sandbox, "start", "D-002")
            self.assertEqual(result.returncode, 0, msg=result.stderr)


class DependsSubcommandTests(unittest.TestCase):
    def test_add_remove_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _run(sandbox, "backlog", "add", "Alvo")
            _run(sandbox, "backlog", "add", "Dep")
            # add
            self.assertEqual(_run(sandbox, "depends", "add", "D-001", "--on", "D-002").returncode, 0)
            self.assertEqual(_depends_on(sandbox, "D-001"), ["D-002"])
            # remove
            self.assertEqual(_run(sandbox, "depends", "remove", "D-001", "--on", "D-002").returncode, 0)
            self.assertEqual(_depends_on(sandbox, "D-001"), [])

    def test_add_self_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _run(sandbox, "feature", "X")
            result = _run(sandbox, "depends", "add", "D-001", "--on", "D-001")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("nao pode depender de si", result.stderr)

    def test_add_nonexistent_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _run(sandbox, "feature", "X")
            result = _run(sandbox, "depends", "add", "D-001", "--on", "D-999")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("nao existe", result.stderr)

    def test_cycle_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _run(sandbox, "feature", "A")
            _run(sandbox, "feature", "B", "--depends-on", "D-001")
            # Tentar declarar D-001 depende de D-002 fecharia A->B->A.
            result = _run(sandbox, "depends", "add", "D-001", "--on", "D-002")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ciclo", result.stderr)

    def test_list_json_marks_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _run(sandbox, "feature", "Dep")
            _run(sandbox, "feature", "Dependente", "--depends-on", "D-001")
            result = _run(sandbox, "depends", "list", "D-002", "--json")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["taskId"], "D-002")
            self.assertEqual(len(payload["dependsOn"]), 1)
            self.assertEqual(payload["dependsOn"][0]["id"], "D-001")
            self.assertTrue(payload["dependsOn"][0]["blocking"])

    def test_list_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _run(sandbox, "feature", "Solo")
            result = _run(sandbox, "depends", "list", "D-001")
            self.assertEqual(result.returncode, 0)
            self.assertIn("nenhuma dependencia", result.stdout)


if __name__ == "__main__":
    unittest.main()
