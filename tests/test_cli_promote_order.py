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
        [sys.executable, "core/src/ai.py", *args],
        cwd=sandbox,
        capture_output=True,
        text=True,
    )


class PromoteOrderTests(unittest.TestCase):
    def test_promote_without_worktree_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed_sandbox(sandbox)
            self.assertEqual(_run(sandbox, "init", "--project-name", "t").returncode, 0)
            self.assertEqual(_run(sandbox, "backlog", "add", "Future").returncode, 0)
            result = _run(sandbox, "promote", "B-001", "--kind", "feature")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            tasks = json.loads((sandbox / ".ai" / "tasks.json").read_text(encoding="utf-8"))
            backlog = json.loads((sandbox / ".ai" / "backlog.json").read_text(encoding="utf-8"))
            self.assertTrue(any(t["id"] == "F-001" for t in tasks["tasks"]))
            self.assertEqual(backlog["items"], [])  # item foi consumido

    def test_promote_failure_keeps_backlog_intact(self) -> None:
        """Sem .git no sandbox, --worktree falha em git_branch_exists.

        Esperado: backlog mantem o B-001 (nao foi consumido).
        """
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed_sandbox(sandbox)
            self.assertEqual(_run(sandbox, "init", "--project-name", "t").returncode, 0)
            self.assertEqual(_run(sandbox, "backlog", "add", "Future").returncode, 0)
            result = _run(
                sandbox,
                "promote",
                "B-001",
                "--kind",
                "feature",
                "--worktree",
                "--branch",
                "ai-process/test-branch",
            )
            # Pode passar OU falhar dependendo do git no sandbox.
            # O que NAO pode acontecer e: backlog vazio + task ausente.
            backlog = json.loads((sandbox / ".ai" / "backlog.json").read_text(encoding="utf-8"))
            tasks = json.loads((sandbox / ".ai" / "tasks.json").read_text(encoding="utf-8"))
            has_task = any(t["id"] == "F-001" for t in tasks["tasks"])
            has_backlog_item = any(it["id"] == "B-001" for it in backlog["items"])
            # invariante: ou criou a task, ou preservou o backlog. Nunca os dois falhos.
            self.assertTrue(has_task or has_backlog_item, msg=result.stderr)


if __name__ == "__main__":
    unittest.main()
