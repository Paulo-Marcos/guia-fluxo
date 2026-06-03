"""F-017: tests for `ai tasks list/show/filter`.

Roda o CLI num sandbox isolado para nao depender da tasks.json do repo.
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
        [sys.executable, "core/src/ai.py", *args],
        cwd=sandbox,
        capture_output=True,
        text=True,
    )


class TasksListTests(unittest.TestCase):
    def _setup_three_tasks(self, sandbox: Path) -> None:
        _seed(sandbox)
        self.assertEqual(_run(sandbox, "init", "--project-name", "t").returncode, 0)
        self.assertEqual(_run(sandbox, "feature", "First").returncode, 0)
        self.assertEqual(_run(sandbox, "issue", "Bug A").returncode, 0)
        self.assertEqual(_run(sandbox, "feature", "Second").returncode, 0)

    def test_list_returns_all(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            self._setup_three_tasks(sandbox)
            result = _run(sandbox, "tasks", "list")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            lines = [l for l in result.stdout.splitlines() if l.startswith(("F-", "I-"))]
            self.assertEqual(len(lines), 3)

    def test_list_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            self._setup_three_tasks(sandbox)
            result = _run(sandbox, "tasks", "list", "--json")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["count"], 3)
            self.assertEqual(len(payload["tasks"]), 3)

    def test_list_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            self._setup_three_tasks(sandbox)
            result = _run(sandbox, "tasks", "list", "--limit", "2")
            self.assertEqual(result.returncode, 0)
            lines = [l for l in result.stdout.splitlines() if l.startswith(("F-", "I-"))]
            self.assertEqual(len(lines), 2)


class TasksShowTests(unittest.TestCase):
    def test_show_existing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _run(sandbox, "feature", "Hello")
            result = _run(sandbox, "tasks", "show", "F-001", "--json")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            task = json.loads(result.stdout)
            self.assertEqual(task["id"], "F-001")
            self.assertEqual(task["title"], "Hello")

    def test_show_missing_exits_1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            result = _run(sandbox, "tasks", "show", "F-999", "--json")
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["found"])


class TasksFilterTests(unittest.TestCase):
    def _setup(self, sandbox: Path) -> None:
        _seed(sandbox)
        _run(sandbox, "init", "--project-name", "t")
        _run(sandbox, "feature", "Feat1")
        _run(sandbox, "issue", "Issue1")
        _run(sandbox, "feature", "Feat2")
        # ready Feat2 para mudar status
        _run(sandbox, "ready", "F-002", "--summary", "ready")

    def test_filter_by_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            self._setup(sandbox)
            result = _run(sandbox, "tasks", "filter", "--status", "Aguardando validacao", "--json")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["count"], 1)
            self.assertEqual(payload["tasks"][0]["id"], "F-002")

    def test_filter_by_kind(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            self._setup(sandbox)
            result = _run(sandbox, "tasks", "filter", "--kind", "issue", "--json")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["count"], 1)
            self.assertEqual(payload["tasks"][0]["kind"], "issue")

    def test_filter_combined(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            self._setup(sandbox)
            result = _run(
                sandbox,
                "tasks",
                "filter",
                "--kind",
                "feature",
                "--status",
                "Em desenvolvimento",
                "--json",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["count"], 1)
            self.assertEqual(payload["tasks"][0]["id"], "F-001")


if __name__ == "__main__":
    unittest.main()
