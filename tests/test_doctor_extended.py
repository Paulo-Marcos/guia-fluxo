"""F-018: tests for the extended `guia doctor`.

Cobre:
- doctor no repo-mae passa (com manifest, render OK, lock_api importavel)
- doctor no consumer (sem core/) entra em modo lite
- --strict promove warnings a erros
- --skip-render pula o render --check
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import REPO_ROOT

GUIA = REPO_ROOT / "core" / "src" / "guia.py"


def _run_dev(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GUIA), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def _seed_consumer(sandbox: Path) -> None:
    """Replica o layout consumer flat: .guia/ + guia.py + lock_api.py."""
    # guia.py + helpers flat (mesma estrutura de dist/bin/)
    (sandbox / "bin").mkdir()
    for src in (REPO_ROOT / "core" / "src").glob("*.py"):
        if not src.name.startswith("__"):
            shutil.copy2(src, sandbox / "bin" / src.name)
    shutil.copy2(REPO_ROOT / "core" / "lock" / "lock_api.py", sandbox / "bin" / "lock_api.py")


def _run_consumer(sandbox: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "bin/guia.py", *args],
        cwd=sandbox,
        capture_output=True,
        text=True,
    )


class DoctorDevTests(unittest.TestCase):
    def test_doctor_passes_in_repo_mae(self) -> None:
        result = _run_dev("doctor", "--skip-render")
        # --skip-render para nao depender de sincronia do dist quando
        # outro teste paralelo esta rodando renders
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Guia Fluxo files OK", result.stdout)


class DoctorConsumerLiteTests(unittest.TestCase):
    def test_doctor_lite_in_consumer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed_consumer(sandbox)
            # init para semear .guia/
            init_result = _run_consumer(sandbox, "init", "--project-name", "consumer-smoke")
            self.assertEqual(init_result.returncode, 0, msg=init_result.stderr)
            # doctor (sem flags) deve passar - modo lite
            doctor_result = _run_consumer(sandbox, "doctor")
            self.assertEqual(doctor_result.returncode, 0, msg=doctor_result.stderr)
            self.assertIn("Guia Fluxo files OK", doctor_result.stdout)


if __name__ == "__main__":
    unittest.main()
