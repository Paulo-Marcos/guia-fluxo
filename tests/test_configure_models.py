"""D-155: as etapas de modelo do configurador.

`models-triage` liga/desliga a triagem (padrao on); `models-normal` escolhe o
modelo das demandas normais (padrao sonnet); `models-fable` e a politica do
Fable (padrao ask: sugere e pergunta). Desligada, a triagem esconde as outras
duas e o `triage` nao grava recomendacao.
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
class ConfigureModelsTests(unittest.TestCase):
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

    def _guia(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run([sys.executable, "core/src/guia.py", *args], cwd=self.sb,
                                capture_output=True, text=True, encoding="utf-8",
                                env={**os.environ, "GUIA_GH_FIXTURE": str(self.fixture)})
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        return result

    def _steps(self, *sets: str) -> dict:
        args = ["configure", "--plan", "--json"] + [a for s in sets for a in ("--set", s)]
        return {s["id"]: s for s in json.loads(self._guia(*args).stdout)["steps"]}

    def test_defaults_and_recommendations(self) -> None:
        steps = self._steps()
        self.assertEqual(steps["models-triage"]["recommended"], "on")
        self.assertEqual(steps["models-normal"]["recommended"], "sonnet")
        self.assertEqual(steps["models-fable"]["recommended"], "ask")
        self.assertIn("pergunta", steps["models-fable"]["explain"])

    def test_off_hides_the_other_model_steps(self) -> None:
        steps = self._steps("models-triage=off")
        self.assertFalse(steps["models-normal"]["applies"])
        self.assertFalse(steps["models-fable"]["applies"])

    def test_writes_the_models_keys_and_triage_follows_them(self) -> None:
        self._guia("configure", "--set", "models-normal=opus", "--set", "models-fable=never", "--yes")
        config = json.loads(self.process.read_text(encoding="utf-8"))
        self.assertEqual(config["models"], {"tiers": {"normal": "opus"}, "fable": "never"})
        self._guia("feature", "Tela de cadastro")
        triage = json.loads(self._guia("triage", "D-001", "--scope", "2", "--json").stdout)["triage"]
        self.assertEqual(triage["model"], "opus")

    def test_triage_off_records_nothing(self) -> None:
        self._guia("configure", "--set", "models-triage=off", "--yes")
        self._guia("bug", "Corrida no worker")
        self.assertIn("triagem desligada", self._guia("triage", "D-001", "--scope", "1").stdout)
        self.assertIsNone(json.loads(self._guia("triage", "D-001", "--json").stdout)["triage"])


if __name__ == "__main__":
    unittest.main()
