"""D-104: `cancel` nao deduz a demanda do current-task.json global.

Mesmo footgun que o D-103 fechou no `finish`: `cancel` sem id caia no ponteiro
`current-task.json`, que e unico por copia de trabalho e drifta entre sessoes/
chats concorrentes na mesma pasta. Como `cancel` e terminal (status -> Cancelada)
e irreversivel, um `cancel` sem id podia cancelar uma demanda que este chat nunca
tocou.

Guard: sem id explicito, `cancel` recusa (nao usa o ponteiro global) e lista as
candidatas abertas (nao-terminais) para o operador escolher a certa. O guard de
status terminal (nao cancela o que ja e terminal) ja existia e segue valendo.

Os testes rodam o CLI real num sandbox temporario, espelhando o harness de
test_finish_id_guard.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import REPO_ROOT

CORE_SRC = REPO_ROOT / "core" / "src"
CORE_LOCK = REPO_ROOT / "core" / "lock"


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
    return result.stdout.split(" ", 1)[0].strip()


def _show(sandbox: Path, task_id: str) -> dict:
    return json.loads(_run(sandbox, "tasks", "show", task_id, "--json").stdout)


class CancelRequiresExplicitIdTests(unittest.TestCase):
    def test_bare_cancel_is_rejected_and_leaves_state_untouched(self) -> None:
        """Sem id, cancel recusa (nao deduz do current-task) e nada muda."""
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            first = _created_id(_run(sandbox, "feature", "Demanda do chat"))

            result = _run(sandbox, "cancel", "--reason", "engano")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("id explicito", result.stderr)
            # A task nao foi cancelada por engano.
            self.assertEqual(_show(sandbox, first)["status"], "Em desenvolvimento")

    def test_bare_cancel_lists_open_candidates(self) -> None:
        """A recusa ajuda: lista as candidatas abertas (nao-terminais)."""
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            parked = _created_id(_run(sandbox, "backlog", "add", "Ideia parada"))

            result = _run(sandbox, "cancel", "--reason", "limpeza")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(parked, result.stderr)
            self.assertIn("nao-terminais", result.stderr)


class CancelStatusGuardTests(unittest.TestCase):
    def test_cancel_accepts_open_task_with_explicit_id(self) -> None:
        """Caminho feliz: id explicito de demanda aberta e cancelado."""
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            target = _created_id(_run(sandbox, "feature", "Cancela esta"))

            result = _run(
                sandbox, "cancel", target, "--reason", "escopo dropado"
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(_show(sandbox, target)["status"], "Cancelada")

    def test_cancel_refuses_terminal_task_even_with_explicit_id(self) -> None:
        """Guard de status: cancelar uma task ja terminal e recusado."""
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            target = _created_id(_run(sandbox, "feature", "Cancela uma vez"))
            _run(sandbox, "cancel", target, "--reason", "primeira")

            result = _run(sandbox, "cancel", target, "--reason", "segunda")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("terminal", result.stderr)


if __name__ == "__main__":
    unittest.main()
