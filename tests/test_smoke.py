"""Smoke test: exercita o caminho feliz da CLI ai num diretorio temporario.

A partir do split modular (F-015), `core/src/ai.py` depende de
`_constants.py`, `_state.py`, `_tasks.py`, etc. e `core/lock/lock_api.py`.
O teste copia tudo para o sandbox preservando o layout do repo-mae para
que o `_bootstrap_sys_path` da CLI ache os modulos.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CORE_SRC = REPO_ROOT / "core" / "src"
LOCK_API = REPO_ROOT / "core" / "lock" / "lock_api.py"


def _seed_sandbox(sandbox: Path) -> None:
    """Replica o layout core/src/ + core/lock/lock_api.py no sandbox."""
    (sandbox / "core" / "src").mkdir(parents=True)
    (sandbox / "core" / "lock").mkdir(parents=True)
    for src in CORE_SRC.glob("*.py"):
        if src.name.startswith("__"):
            continue
        shutil.copy2(src, sandbox / "core" / "src" / src.name)
    shutil.copy2(LOCK_API, sandbox / "core" / "lock" / LOCK_API.name)


class SmokeTest(unittest.TestCase):
    def test_fluxo_basico(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed_sandbox(sandbox)

            def run(*args: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [sys.executable, "core/src/ai.py", *args],
                    cwd=sandbox,
                    check=True,
                    capture_output=True,
                    text=True,
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
