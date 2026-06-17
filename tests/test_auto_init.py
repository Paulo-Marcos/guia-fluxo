"""Auto-init + CWD-aware project root (D-075).

The Claude Code plugin install ships the engine outside the consumer
project (in the plugin cache, reached via `${CLAUDE_PLUGIN_ROOT}`), and the
agent runs commands from the project directory. These tests pin the two
behaviors that make that work without a clone:

  1. The engine roots `.guia/` at the caller's CWD (the consumer project),
     not at the script location.
  2. The first state-touching command auto-creates `.guia/` (no manual
     `init`).
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


def _seed_engine_flat(bin_dir: Path) -> None:
    """Replica o layout flat de dist/bin/ (motor fora do projeto)."""
    bin_dir.mkdir(parents=True)
    for src in CORE_SRC.glob("*.py"):
        if src.name.startswith("__"):
            continue
        shutil.copy2(src, bin_dir / src.name)
    shutil.copy2(LOCK_API, bin_dir / LOCK_API.name)


class AutoInitTest(unittest.TestCase):
    def test_roots_guia_at_cwd_not_engine_location(self) -> None:
        """Motor fora do projeto + cwd=projeto -> .guia/ nasce no projeto."""
        with tempfile.TemporaryDirectory() as cache_tmp, tempfile.TemporaryDirectory() as project_tmp:
            engine_bin = Path(cache_tmp) / "plugin" / "bin"
            _seed_engine_flat(engine_bin)
            project = Path(project_tmp)

            result = subprocess.run(
                [sys.executable, str(engine_bin / "guia.py"), "feature", "auto-init smoke"],
                cwd=project,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(
                result.returncode,
                0,
                msg=f"feature falhou: stdout={result.stdout!r} stderr={result.stderr!r}",
            )

            # .guia/ deve nascer no projeto (cwd), nao na pasta do motor.
            self.assertTrue((project / ".guia" / "process.json").is_file())
            self.assertTrue((project / ".guia" / "tasks.json").is_file())
            self.assertFalse(
                (engine_bin.parent / ".guia").exists(),
                ".guia/ vazou para a pasta do motor (deveria rootar no projeto)",
            )

            tasks = json.loads((project / ".guia" / "tasks.json").read_text(encoding="utf-8"))
            self.assertTrue(any(t["title"] == "auto-init smoke" for t in tasks["tasks"]))

    def test_auto_init_announced_on_stderr(self) -> None:
        """Primeiro comando num projeto virgem avisa que inicializou."""
        with tempfile.TemporaryDirectory() as cache_tmp, tempfile.TemporaryDirectory() as project_tmp:
            engine_bin = Path(cache_tmp) / "plugin" / "bin"
            _seed_engine_flat(engine_bin)
            project = Path(project_tmp)

            result = subprocess.run(
                [sys.executable, str(engine_bin / "guia.py"), "backlog", "list"],
                cwd=project,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("inicializado automaticamente", result.stderr)

    def test_doctor_does_not_auto_init(self) -> None:
        """`doctor` num projeto virgem reporta falta de .guia/, nao a cria."""
        with tempfile.TemporaryDirectory() as cache_tmp, tempfile.TemporaryDirectory() as project_tmp:
            engine_bin = Path(cache_tmp) / "plugin" / "bin"
            _seed_engine_flat(engine_bin)
            project = Path(project_tmp)

            result = subprocess.run(
                [sys.executable, str(engine_bin / "guia.py"), "doctor"],
                cwd=project,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertNotEqual(result.returncode, 0, "doctor deveria falhar sem .guia/")
            self.assertFalse(
                (project / ".guia").exists(),
                "doctor nao deve criar .guia/ (mascararia o diagnostico)",
            )

    def test_guia_project_root_override(self) -> None:
        """GUIA_PROJECT_ROOT redireciona a raiz independente de cwd."""
        import os

        with tempfile.TemporaryDirectory() as cache_tmp, \
                tempfile.TemporaryDirectory() as cwd_tmp, \
                tempfile.TemporaryDirectory() as root_tmp:
            engine_bin = Path(cache_tmp) / "plugin" / "bin"
            _seed_engine_flat(engine_bin)
            override_root = Path(root_tmp)

            env = dict(os.environ)
            env["GUIA_PROJECT_ROOT"] = str(override_root)
            result = subprocess.run(
                [sys.executable, str(engine_bin / "guia.py"), "feature", "override smoke"],
                cwd=cwd_tmp,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((override_root / ".guia" / "tasks.json").is_file())
            self.assertFalse((Path(cwd_tmp) / ".guia").exists())


if __name__ == "__main__":
    unittest.main()
