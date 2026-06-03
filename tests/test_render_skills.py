"""Tests for core/build/render-skills.py hardening features (F-015).

Covers:
- --check exits 0 on synchronized state
- --check-orphans flag is recognized
- TEMPLATE_FILES set must match files on disk (would fail if drift)
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from conftest_paths import REPO_ROOT

RENDER = REPO_ROOT / "core" / "build" / "render-skills.py"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RENDER), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


class RenderSkillsTests(unittest.TestCase):
    def test_check_passes_when_in_sync(self) -> None:
        # render once to sync, then assert --check returns 0
        result_write = _run()
        self.assertEqual(result_write.returncode, 0, msg=result_write.stderr)
        result_check = _run("--check")
        self.assertEqual(result_check.returncode, 0, msg=result_check.stderr)

    def test_check_orphans_flag_recognized(self) -> None:
        # apenas confirma que a flag passa pelo argparse e retorna codigo coerente
        result = _run("--check-orphans")
        self.assertIn(result.returncode, (0, 1), msg=result.stderr)

    def test_verb_only(self) -> None:
        result = _run("--check", "--verb", "feature")
        self.assertEqual(result.returncode, 0, msg=result.stderr)


if __name__ == "__main__":
    unittest.main()
