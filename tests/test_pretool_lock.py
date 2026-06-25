"""PreToolUse hook (D-102): `check-lock.py pretool`.

Spawns the script with a PreToolUse-shaped JSON payload on stdin and a
sandboxed project (`cwd` in the payload points the lock domain at it).
Pins the contract:

  * Editing a locked file -> exit 2 + reason on stderr (Claude Code blocks).
  * Editing a free file -> exit 0 (allow).
  * Creating a NEW file -> exit 0: the default blanket `add` lock on `*`
    must NOT block edits, only the commit-msg hook gates additions.
  * Any infra failure (malformed JSON, no file_path) -> exit 0 (fail-open).
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import REPO_ROOT

CHECK_LOCK = REPO_ROOT / "core" / "lock" / "check-lock.py"

_BLANKET_ADD = """version: 1
locks:
- id: adicoes-exigem-autorizacao
  description: Qualquer arquivo novo exige autorizacao explicita
  operations: [add]
  files:
  - '*'
"""

_SPECIFIC_MODIFY = """version: 1
locks:
- id: homologado
  description: Modulo homologado, nao editar sem autorizacao
  operations: [add, modify, delete, rename]
  files:
  - src/protected.py
"""


def _run_pretool(payload: dict, *, raw_stdin: str | None = None):
    stdin = raw_stdin if raw_stdin is not None else json.dumps(payload)
    return subprocess.run(
        [sys.executable, str(CHECK_LOCK), "pretool"],
        input=stdin,
        capture_output=True,
        text=True,
    )


class PretoolLockTests(unittest.TestCase):
    def _sandbox(self, registry_body: str) -> Path:
        project = Path(tempfile.mkdtemp()).resolve()
        locks = project / ".guia" / "locks"
        locks.mkdir(parents=True)
        (locks / "registry.yaml").write_text(registry_body, encoding="utf-8")
        return project

    def _payload(self, project: Path, file_path: Path, tool: str = "Edit") -> dict:
        return {
            "session_id": "test",
            "hook_event_name": "PreToolUse",
            "tool_name": tool,
            "tool_input": {"file_path": str(file_path)},
            "cwd": str(project),
        }

    def test_locked_file_is_blocked(self) -> None:
        project = self._sandbox(_SPECIFIC_MODIFY)
        target = project / "src" / "protected.py"
        target.parent.mkdir(parents=True)
        target.write_text("# homologado\n", encoding="utf-8")
        result = _run_pretool(self._payload(project, target))
        self.assertEqual(result.returncode, 2, msg=result.stderr)
        self.assertIn("homologado", result.stderr)
        self.assertIn("travados", result.stderr.lower())

    def test_free_file_passes(self) -> None:
        project = self._sandbox(_SPECIFIC_MODIFY)
        target = project / "src" / "other.py"
        target.parent.mkdir(parents=True)
        target.write_text("x = 1\n", encoding="utf-8")
        result = _run_pretool(self._payload(project, target))
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_new_file_write_not_blocked_by_blanket_add_lock(self) -> None:
        # The default registry blocks `add` on `*`; the PreToolUse hook checks
        # `modify` only, so creating a new file must NOT be blocked here (the
        # commit-msg hook is the gate for additions).
        project = self._sandbox(_BLANKET_ADD)
        target = project / "brand_new.py"  # does not exist
        result = _run_pretool(self._payload(project, target, tool="Write"))
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_multiedit_on_locked_file_is_blocked(self) -> None:
        project = self._sandbox(_SPECIFIC_MODIFY)
        target = project / "src" / "protected.py"
        target.parent.mkdir(parents=True)
        target.write_text("# homologado\n", encoding="utf-8")
        result = _run_pretool(self._payload(project, target, tool="MultiEdit"))
        self.assertEqual(result.returncode, 2, msg=result.stderr)

    def test_malformed_json_degrades_open(self) -> None:
        result = _run_pretool({}, raw_stdin="{ this is not json")
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_empty_stdin_degrades_open(self) -> None:
        result = _run_pretool({}, raw_stdin="")
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_missing_file_path_passes(self) -> None:
        project = self._sandbox(_SPECIFIC_MODIFY)
        payload = {
            "tool_name": "Edit",
            "tool_input": {},  # no file_path
            "cwd": str(project),
        }
        result = _run_pretool(payload)
        self.assertEqual(result.returncode, 0, msg=result.stderr)


if __name__ == "__main__":
    unittest.main()
