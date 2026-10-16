"""D-181: arquivo no disco mas fora do HEAD e `add`, como o hook do commit ve.

Regressao: `check` e o PreToolUse decidiam add x modify pelo disco. Um teste
novo, ja escrito e ainda nao commitado, saia como `modify` numa trava que so
guarda modify/delete/rename (`testes-sao-contrato`), e o chat parava para pedir
um unlock que o hook do commit (status A) nunca exigiria.
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

sys.path.insert(0, str(Path(__file__).resolve().parent))

from conftest_paths import REPO_ROOT  # noqa: E402

CHECK_LOCK = REPO_ROOT / "core" / "lock" / "check-lock.py"

_TESTS_CONTRACT = """version: 1
locks:
- id: testes-sao-contrato
  description: Testes garantem o comportamento
  operations: [modify, delete, rename]
  files:
  - 'tests/*'
"""


def _git(project: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=project, check=True, capture_output=True)


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class UntrackedFileIsAddTests(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.project = Path(tmp.name).resolve()
        locks = self.project / ".guia" / "locks"
        locks.mkdir(parents=True)
        (locks / "registry.yaml").write_text(_TESTS_CONTRACT, encoding="utf-8")
        (self.project / "tests").mkdir()
        (self.project / "tests" / "test_old.py").write_text("def test_x(): pass\n", encoding="utf-8")
        _git(self.project, "init", "-q")
        _git(self.project, "add", "-A")
        _git(self.project, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base")
        (self.project / "tests" / "test_new.py").write_text("def test_y(): pass\n", encoding="utf-8")

    def _check(self, *files: str) -> subprocess.CompletedProcess:
        env = {**os.environ, "GUIA_PROJECT_ROOT": str(self.project)}
        return subprocess.run([sys.executable, str(CHECK_LOCK), "check", "--json", *files],
                              cwd=self.project, env=env, capture_output=True, text=True)

    def _pretool(self, target: Path) -> subprocess.CompletedProcess:
        payload = {"hook_event_name": "PreToolUse", "tool_name": "Edit",
                   "tool_input": {"file_path": str(target)}, "cwd": str(self.project)}
        return subprocess.run([sys.executable, str(CHECK_LOCK), "pretool"],
                              input=json.dumps(payload), capture_output=True, text=True)

    def test_check_treats_an_uncommitted_new_test_as_add(self) -> None:
        result = self._check("tests/test_new.py")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertTrue(json.loads(result.stdout)["ok"])

    def test_check_still_blocks_a_committed_test(self) -> None:
        result = self._check("tests/test_old.py")
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["blocked"][0]["operation"], "modify")

    def test_editing_the_new_test_again_is_not_blocked(self) -> None:
        self.assertEqual(self._pretool(self.project / "tests" / "test_new.py").returncode, 0)
        self.assertEqual(self._pretool(self.project / "tests" / "test_old.py").returncode, 2)


if __name__ == "__main__":
    unittest.main()
