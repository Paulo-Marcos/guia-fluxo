"""D-096 (B-018): aviso quando um comando cai no fallback do current-task.json
global e ha 2+ tasks ativas ao mesmo tempo.

Diferente de test_status_all (que cobre o aviso no `status --all`), aqui o foco
e o caminho generico `find_task_or_current(None)`: qualquer comando sem id
explicito (ex: `status` sem argumento) deve avisar em stderr quando a escolha do
current-task global e ambigua, e ficar silencioso quando ha no maximo uma task
ativa ou quando o id e passado explicitamente.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import REPO_ROOT

CORE_SRC = REPO_ROOT / "core" / "src"
CORE_LOCK = REPO_ROOT / "core" / "lock"

WARN_MARKER = "current-task.json global"


def _seed(sandbox: Path) -> None:
    (sandbox / "core" / "src").mkdir(parents=True)
    (sandbox / "core" / "lock").mkdir(parents=True)
    for src in CORE_SRC.glob("*.py"):
        if not src.name.startswith("__"):
            shutil.copy2(src, sandbox / "core" / "src" / src.name)
    shutil.copy2(CORE_LOCK / "lock_api.py", sandbox / "core" / "lock" / "lock_api.py")


def _run(sandbox: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "core/src/guia.py", *args],
        cwd=sandbox,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _created_id(result: subprocess.CompletedProcess[str]) -> str:
    # stdout comeca com "D-NNN created: ..."
    return result.stdout.split(" ", 1)[0].strip()


class CurrentTaskFallbackTests(unittest.TestCase):
    def test_two_active_no_id_warns_on_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _run(sandbox, "feature", "First active")
            second = _created_id(_run(sandbox, "feature", "Second active"))
            # `status` sem id cai no fallback do current-task global.
            result = _run(sandbox, "status")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn(WARN_MARKER, result.stderr)
            self.assertIn("2 tasks em desenvolvimento", result.stderr)
            # Avisa qual id foi escolhido (o current = ultimo criado).
            self.assertIn(second, result.stderr)
            # stdout JSON nao e poluido pelo aviso.
            self.assertNotIn(WARN_MARKER, result.stdout)

    def test_single_active_no_id_is_silent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _run(sandbox, "feature", "Only one")
            result = _run(sandbox, "status")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertNotIn(WARN_MARKER, result.stderr)

    def test_two_active_explicit_id_is_silent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            first = _created_id(_run(sandbox, "feature", "First active"))
            _run(sandbox, "feature", "Second active")
            # Id explicito desliga o fallback ambiguo -> sem aviso.
            result = _run(sandbox, "status", first)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertNotIn(WARN_MARKER, result.stderr)


if __name__ == "__main__":
    unittest.main()
