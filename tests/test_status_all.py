"""B-014: tests for `guia status --all` (quadro de tasks em desenvolvimento).

Tambem cobre o aviso de concorrencia (B-018): quando ha 2+ tasks ativas,
o comando avisa sobre a ambiguidade do current-task.json global.
"""

from __future__ import annotations

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


class StatusAllTests(unittest.TestCase):
    def test_all_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            result = _run(sandbox, "status", "--all")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("Nenhuma task em desenvolvimento", result.stdout)

    def test_all_single_marks_current(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _run(sandbox, "feature", "Only one")
            result = _run(sandbox, "status", "--all")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            lines = [l for l in result.stdout.splitlines() if l.startswith("D-")]
            self.assertEqual(len(lines), 1)
            self.assertIn("<- current", result.stdout)
            # Sem aviso de concorrencia com uma so task.
            self.assertNotIn("ao mesmo tempo", result.stdout)

    def test_all_two_active_warns_concurrency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _run(sandbox, "feature", "First active")
            _run(sandbox, "feature", "Second active")
            result = _run(sandbox, "status", "--all")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            lines = [l for l in result.stdout.splitlines() if l.startswith("D-")]
            self.assertEqual(len(lines), 2)
            self.assertIn("2 tasks em desenvolvimento ao mesmo tempo", result.stdout)
            self.assertIn("B-018", result.stdout)


if __name__ == "__main__":
    unittest.main()
