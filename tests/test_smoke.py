"""Smoke test: exercita o caminho feliz da CLI ai num diretorio temporario."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AI_SCRIPT = REPO_ROOT / "scripts" / "ai.py"


class SmokeTest(unittest.TestCase):
    def test_fluxo_basico(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            (sandbox / "scripts").mkdir()
            shutil.copy2(AI_SCRIPT, sandbox / "scripts" / "ai.py")

            def run(*args: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [sys.executable, "scripts/ai.py", *args],
                    cwd=sandbox, check=True, capture_output=True, text=True,
                )

            run("init", "--project-name", "smoke")
            run("feature", "smoke")
            run("ready", "F-001", "--summary", "smoke entregue")
            run("finish", "F-001", "--no-commit", "--summary", "smoke fechado")

            tasks = json.loads((sandbox / ".ai" / "tasks.json").read_text(encoding="utf-8"))
            task = next(t for t in tasks["tasks"] if t["id"] == "F-001")
            self.assertEqual(task["status"], "Validada")


if __name__ == "__main__":
    unittest.main()
