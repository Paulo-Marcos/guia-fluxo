"""D-144: o painel do terminal do configurador (epico E-008).

`guia configure` num terminal (ou com `--interactive`) pergunta uma etapa por
vez: Enter aceita a recomendada, numero escolhe a opcao, `m` mantem, `q` sai
sem gravar, texto vira o valor. O plano segue as respostas (escolher `direct`
some com as etapas do modo pr). Nada e gravado sem o `s` final.
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


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=", *args],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8",
    )


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class ConfigureTerminalTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.main = base / "app"
        (self.main / "core" / "src").mkdir(parents=True)
        (self.main / "core" / "lock").mkdir(parents=True)
        for src in CORE_SRC.glob("*.py"):
            if not src.name.startswith("__"):
                shutil.copy2(src, self.main / "core" / "src" / src.name)
        shutil.copy2(CORE_LOCK / "lock_api.py", self.main / "core" / "lock" / "lock_api.py")
        (self.main / ".guia").mkdir()
        self.process = self.main / ".guia" / "process.json"
        self.process.write_text(json.dumps({"projectName": "app"}), encoding="utf-8")
        (self.main / ".gitignore").write_text(".guia/\ncore/\n", encoding="utf-8")
        for args in (("init", "-q", "-b", "main"), ("add", "."), ("commit", "-q", "-m", "init")):
            self.assertEqual(_git(self.main, *args).returncode, 0, msg=str(args))
        self.fixture = base / "gh.json"
        self.fixture.write_text(json.dumps({"__auth__": True}), encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _talk(self, *lines: str, flags: tuple[str, ...] = ()) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "core/src/guia.py", "configure", "--interactive", *flags],
            cwd=self.main, input="\n".join(lines) + "\n", capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "GUIA_GH_FIXTURE": str(self.fixture)},
        )

    def _prompts(self, *sets: str) -> int:
        """Quantas etapas o painel pergunta com estas respostas (o plano decide)."""
        args = [arg for value in sets for arg in ("--set", value)]
        out = subprocess.run(
            [sys.executable, "core/src/guia.py", "configure", "--plan", "--json", *args],
            cwd=self.main, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "GUIA_GH_FIXTURE": str(self.fixture)},
        ).stdout
        return sum(1 for step in json.loads(out)["steps"] if step["applies"])

    def _config(self) -> dict:
        return json.loads(self.process.read_text(encoding="utf-8"))

    def test_direct_hides_the_pr_steps_and_writes_on_yes(self) -> None:
        # 1 = direct na etapa do modo; Enter aceita o resto; "s" grava.
        result = self._talk("1", *[""] * (self._prompts("mode=direct") - 1), "s")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertNotIn("Portao do ship", result.stdout, "modo direct: sem as etapas do pr")
        self.assertEqual(self._config()["delivery"]["mode"], "direct")
        self.assertTrue(list((self.main / ".guia" / "backups").iterdir()))

    def test_pr_shows_its_steps_and_typed_values(self) -> None:
        rest = self._prompts("mode=pr") - 7  # modo, 5 etapas, portao
        lines = ["2", "", "", "", "", "", "pytest -q, npm test"] + [""] * rest + ["s"]
        result = self._talk(*lines)
        self.assertIn("Portao do ship", result.stdout)
        config = self._config()
        self.assertEqual(config["delivery"]["mode"], "pr")
        self.assertEqual(config["delivery"]["gate"]["full"], ["pytest -q", "npm test"])

    def test_no_means_nothing_written(self) -> None:
        result = self._talk("2", *[""] * (self._prompts("mode=pr") - 1), "n")
        self.assertIn("Nada gravado", result.stdout)
        self.assertNotIn("delivery", self._config())

    def test_q_quits_without_writing(self) -> None:
        result = self._talk("2", "q")
        self.assertIn("Saiu sem gravar", result.stdout)
        self.assertNotIn("delivery", self._config())

    def test_bad_value_asks_again(self) -> None:
        result = self._talk("talvez", "1", *[""] * (self._prompts("mode=direct") - 1), "s")
        self.assertIn("tente de novo", result.stdout)
        self.assertEqual(self._config()["delivery"]["mode"], "direct")

    def test_pending_only_skips_what_is_settled(self) -> None:
        self.process.write_text(json.dumps({"delivery": {"mode": "direct"}, "autonomy": {"default": "manual", "ceiling": "queue"}}),
                                encoding="utf-8")
        result = self._talk(*[""] * 15, "n", flags=("--pendentes",))
        self.assertNotIn("Modo de entrega", result.stdout, "ja decidido e igual a recomendacao")


if __name__ == "__main__":
    unittest.main()
