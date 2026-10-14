"""PreToolUse: criar arquivo novo e `add`, nao `modify` (D-158).

Regressao: o hook tratava todo Write como `modify`. Com um lock `modify`
em `tests/*` (perfil `testes` do init), criar um teste NOVO era barrado -
o oposto do que o perfil promete. Editar um teste existente segue barrado.
"""

from __future__ import annotations

import json
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


class PretoolNewFileIsAddTests(unittest.TestCase):
    def _run(self, project: Path, target: Path, tool: str) -> subprocess.CompletedProcess:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": tool,
            "tool_input": {"file_path": str(target)},
            "cwd": str(project),
        }
        return subprocess.run(
            [sys.executable, str(CHECK_LOCK), "pretool"],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
        )

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.project = Path(tmp.name).resolve()
        locks = self.project / ".guia" / "locks"
        locks.mkdir(parents=True)
        (locks / "registry.yaml").write_text(_TESTS_CONTRACT, encoding="utf-8")
        (self.project / "tests").mkdir()

    def test_creating_new_test_passes(self) -> None:
        result = self._run(self.project, self.project / "tests" / "test_new.py", "Write")
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_editing_existing_test_is_blocked(self) -> None:
        target = self.project / "tests" / "test_old.py"
        target.write_text("def test_x(): pass\n", encoding="utf-8")
        for tool in ("Edit", "Write"):
            result = self._run(self.project, target, tool)
            self.assertEqual(result.returncode, 2, msg=f"{tool}: {result.stderr}")
            self.assertIn("testes-sao-contrato", result.stderr)


if __name__ == "__main__":
    unittest.main()
