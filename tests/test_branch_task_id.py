"""D-110: no modo `pr`, a demanda sem id se resolve pela branch (R3).

Dentro de `d-NNN-*`, `status`, `ready` e `finish` sem id resolvem para a
D-NNN, antes do `current-task.json` global (que outra sessao pode ter
movido, D-103). `cancel` segue exigindo id. Fora de branch de demanda, ou no
modo `direct`, nada muda.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import CORE_LOCK, CORE_SRC


def _seed_engine_flat(bin_dir: Path) -> None:
    bin_dir.mkdir(parents=True)
    for src in CORE_SRC.glob("*.py"):
        if not src.name.startswith("__"):
            shutil.copy2(src, bin_dir / src.name)
    shutil.copy2(CORE_LOCK / "lock_api.py", bin_dir / "lock_api.py")


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


class BranchTaskIdTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.engine = base / "plugin" / "bin"
        _seed_engine_flat(self.engine)
        self.main = base / "main"
        self.worktree = base / "main-d001"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _setup(self, mode: str) -> None:
        """D-001 com worktree em `d-001-x`; D-002 criada depois (vira o ponteiro)."""
        (self.main / ".guia").mkdir(parents=True)
        (self.main / ".guia" / "process.json").write_text(
            json.dumps({"delivery": {"mode": mode}}), encoding="utf-8"
        )
        (self.main / ".gitignore").write_text(
            ".guia/*.json\n!.guia/process.json\n.guia/*.md\n.guia/*.txt\n.guia/reports/\n",
            encoding="utf-8",
        )
        _git(self.main, "init", "-q", "-b", "main")
        _git(self.main, "add", ".")
        _git(self.main, "commit", "-q", "-m", "init")
        self._ok(self.main, "chore", "primeira")
        _git(self.main, "worktree", "add", "-q", str(self.worktree), "-b", "d-001-primeira")
        self._ok(self.main, "chore", "segunda")

    def _run(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.engine / "guia.py"), *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def _ok(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        result = self._run(cwd, *args)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    @staticmethod
    def _shown_id(result: subprocess.CompletedProcess[str]) -> str | None:
        """Id do JSON que o `status` imprime antes da linha NOME DA DEMANDA."""
        data, _ = json.JSONDecoder().raw_decode(result.stdout)
        return data.get("id")

    def _status_of(self, task_id: str) -> str:
        tasks = json.loads((self.main / ".guia" / "tasks.json").read_text(encoding="utf-8"))
        return next(t["status"] for t in tasks["tasks"] if t["id"] == task_id)

    def test_status_without_id_uses_branch_over_pointer(self) -> None:
        self._setup("pr")
        result = self._ok(self.worktree, "status")
        self.assertEqual(self._shown_id(result), "D-001")
        self.assertIn("pela branch", result.stderr)

    def test_ready_and_finish_without_id_use_branch(self) -> None:
        self._setup("pr")
        self._ok(self.worktree, "ready", "--summary", "s", "--validation", "v")
        self.assertEqual(self._status_of("D-001"), "Aguardando validacao")
        self._ok(self.worktree, "finish", "--no-commit", "--quality-skip", "teste")
        self.assertEqual(self._status_of("D-001"), "Validada")
        self.assertEqual(self._status_of("D-002"), "Em desenvolvimento")

    def test_cancel_still_requires_id(self) -> None:
        self._setup("pr")
        result = self._run(self.worktree, "cancel", "--reason", "x")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self._status_of("D-001"), "Em desenvolvimento")

    def test_direct_mode_ignores_branch(self) -> None:
        self._setup("direct")
        # No direct o worktree tem estado proprio (vazio): sem id, o status
        # falha como antes; o que importa e nao resolver pela branch.
        result = self._run(self.worktree, "status")
        self.assertNotIn("pela branch", result.stderr)
        if result.returncode == 0:
            self.assertNotEqual(self._shown_id(result), "D-001")

    def test_main_branch_keeps_pointer(self) -> None:
        self._setup("pr")
        result = self._ok(self.main, "status")
        self.assertEqual(self._shown_id(result), "D-002")


if __name__ == "__main__":
    unittest.main()
