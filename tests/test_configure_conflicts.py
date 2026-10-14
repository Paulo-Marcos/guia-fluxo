"""D-166: a etapa "O que a fila faz com conflito" do configurador.

So no modo pr; recomenda `manager` (o gerente da fila resolve) e grava em
`delivery.queue.conflicts`. `return` mantem o comportamento de devolver ao autor.
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

from conftest_paths import CORE_LOCK, CORE_SRC


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class ConfigureConflictsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.sb = Path(self._tmp.name)
        (self.sb / "core" / "src").mkdir(parents=True)
        (self.sb / "core" / "lock").mkdir(parents=True)
        for src in CORE_SRC.glob("*.py"):
            if not src.name.startswith("__"):
                shutil.copy2(src, self.sb / "core" / "src" / src.name)
        shutil.copy2(CORE_LOCK / "lock_api.py", self.sb / "core" / "lock" / "lock_api.py")
        subprocess.run(["git", "init", "-q"], cwd=self.sb, check=True, capture_output=True)
        (self.sb / ".guia").mkdir()
        self.process = self.sb / ".guia" / "process.json"
        self.process.write_text(json.dumps({"projectName": "app"}), encoding="utf-8")
        self.fixture = self.sb / "gh.json"
        self.fixture.write_text(json.dumps({"__auth__": True}), encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _configure(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run([sys.executable, "core/src/guia.py", "configure", *args], cwd=self.sb,
                                capture_output=True, text=True, encoding="utf-8",
                                env={**os.environ, "GUIA_GH_FIXTURE": str(self.fixture)})
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        return result

    def _step(self, *sets: str) -> dict:
        args = ["--plan", "--json"] + [a for s in sets for a in ("--set", s)]
        steps = json.loads(self._configure(*args).stdout)["steps"]
        return next(s for s in steps if s["id"] == "queue-conflicts")

    def test_only_in_pr_mode_and_recommends_the_manager(self) -> None:
        self.assertFalse(self._step()["applies"], "modo direct: sem fila")
        step = self._step("mode=pr")
        self.assertTrue(step["applies"])
        self.assertEqual(step["recommended"], "manager")
        self.assertIn("gerente", step["explain"])

    def test_writes_the_queue_conflicts_key(self) -> None:
        self._configure("--set", "mode=pr", "--set", "queue-conflicts=manager", "--yes")
        config = json.loads(self.process.read_text(encoding="utf-8"))
        self.assertEqual(config["delivery"]["queue"]["conflicts"], "manager")


if __name__ == "__main__":
    unittest.main()
