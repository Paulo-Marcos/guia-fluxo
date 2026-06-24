"""D-080: `finish` exige previa autorizacao humana, garantido pela ferramenta.

Antes, "finish e humano" era so convencao em AGENTS.md - nada tecnico impedia
um agente de rodar `finish`/commit. Agora o proprio CLI recusa o finish sem a
previa autorizacao do desenvolvedor, expressa pela env GUIA_HUMAN_FINISH=1
setada na sessao dele. Com a env presente, o finish prossegue; sem ela, recusa.

Estes testes rodam o CLI real num sandbox temporario com auto-init (sem deploy
de hooks/locks).
"""

from __future__ import annotations

import json
import os
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


def _run(
    sandbox: Path, *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    run_env = {**os.environ}
    # Garante que a env humana nao vaza do ambiente do teste para o sandbox.
    run_env.pop("GUIA_HUMAN_FINISH", None)
    if env:
        run_env.update(env)
    return subprocess.run(
        [sys.executable, "core/src/guia.py", *args],
        cwd=sandbox,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=run_env,
    )


def _status(sandbox: Path, task_id: str) -> str:
    result = _run(sandbox, "tasks", "show", task_id, "--json")
    return json.loads(result.stdout)["status"]


class FinishHumanGateTests(unittest.TestCase):
    def test_finish_refused_without_authorization(self) -> None:
        """Sem a env de autorizacao, finish recusa e nao muda o status da task."""
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "chore", "Mexe em algo")

            result = _run(
                sandbox, "finish", "D-001", "--no-commit", "--docs-skip", "n/a"
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("previa autorizacao", result.stderr)
            self.assertIn("GUIA_HUMAN_FINISH", result.stderr)
            # Status intacto: o gate barra antes de qualquer mutacao.
            self.assertEqual(_status(sandbox, "D-001"), "Em desenvolvimento")

    def test_finish_accepted_with_env(self) -> None:
        """Com GUIA_HUMAN_FINISH=1 (previa autorizacao) o finish prossegue."""
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "chore", "Mexe em algo")

            result = _run(
                sandbox,
                "finish",
                "D-001",
                "--no-commit",
                "--docs-skip",
                "n/a",
                env={"GUIA_HUMAN_FINISH": "1"},
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(_status(sandbox, "D-001"), "Validada")


if __name__ == "__main__":
    unittest.main()
