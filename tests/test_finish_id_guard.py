"""D-103: `finish` nao deduz a demanda do current-task.json global e so fecha
de um estado finalizavel.

Incidente que motivou: `finish` sem id caiu no ponteiro `current-task.json`, que
tinha driftado (outra sessao na mesma pasta) para uma demanda em Backlog de outro
chat, e finalizou a task errada. O ponteiro e unico por copia de trabalho, entao
qualquer chat concorrente pode sobrescreve-lo.

Dois guards fecham o footgun:

1. Resolucao: sem id explicito, `finish` recusa (nao usa o ponteiro global) e
   lista as candidatas em Aguardando validacao.
2. Status: com id, `finish` so aceita demanda em [Aguardando validacao,
   Em desenvolvimento] - finalizar por engano uma Backlog/Planejada (o estado da
   task driftada no incidente) e recusado antes de qualquer mutacao.

Os testes rodam o CLI real num sandbox temporario, espelhando o harness de
test_finish_commit / test_current_task_fallback.
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


class FinishRequiresExplicitIdTests(unittest.TestCase):
    def test_bare_finish_is_rejected_and_leaves_state_untouched(self) -> None:
        """Sem id, finish recusa (nao deduz do current-task) e nada muda."""
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            first = _created_id(_run(sandbox, "feature", "Demanda do chat"))

            result = _run(sandbox, "finish", "--no-commit", "--quality-skip", "n/a")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("id explicito", result.stderr)
            # A task nao foi finalizada por engano.
            self.assertEqual(_show(sandbox, first)["status"], "Em desenvolvimento")

    def test_bare_finish_lists_awaiting_validation_candidates(self) -> None:
        """A recusa ajuda: lista as candidatas em Aguardando validacao."""
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            target = _created_id(_run(sandbox, "feature", "Pronta pra validar"))
            _run(sandbox, "ready", target)

            result = _run(sandbox, "finish", "--no-commit", "--quality-skip", "n/a")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(target, result.stderr)
            self.assertIn("Aguardando validacao", result.stderr)


class FinishStatusGuardTests(unittest.TestCase):
    def test_finish_refuses_backlog_task_even_with_explicit_id(self) -> None:
        """Guard de status: o estado da task driftada no incidente era Backlog;
        finalizar uma Backlog (mesmo com id) e recusado na raiz."""
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            parked = _created_id(_run(sandbox, "backlog", "add", "Ideia parada"))

            result = _run(
                sandbox, "finish", parked, "--no-commit", "--quality-skip", "n/a"
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Backlog", result.stderr)
            self.assertEqual(_show(sandbox, parked)["status"], "Backlog")

    def test_finish_accepts_awaiting_validation_with_explicit_id(self) -> None:
        """Caminho feliz: id explicito de demanda em Aguardando validacao fecha."""
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            target = _created_id(_run(sandbox, "feature", "Fecha esta"))
            _run(sandbox, "ready", target)

            result = _run(
                sandbox, "finish", target, "--no-commit", "--quality-skip", "n/a"
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(_show(sandbox, target)["status"], "Validada")


if __name__ == "__main__":
    unittest.main()
