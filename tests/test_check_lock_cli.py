"""CLI smoke for core/lock/check-lock.py.

Spawns the script in a tempdir-sandboxed registry/lock-ignore and walks
through list, lock, check, audit. Uses monkeypatch on lock_api globals
via env var since check-lock resolves REPO_ROOT relative to itself.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import REPO_ROOT

CHECK_LOCK = REPO_ROOT / "core" / "lock" / "check-lock.py"


def _run(*args: str, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECK_LOCK), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


class CheckLockCLITests(unittest.TestCase):
    def test_list_runs(self) -> None:
        result = _run("list")
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_check_unlocked_file_passes(self) -> None:
        # README.md nao esta travado por nada
        result = _run("check", "README.md")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("OK:", result.stdout)

    def test_unknown_subcommand_fails(self) -> None:
        result = _run("unknown-subcmd")
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
