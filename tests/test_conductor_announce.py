"""D-176: toda etapa termina com o proximo passo, e o condutor sabe do executor.

Quem chama o motor direto (sem o texto da skill ready) recebia so "moved to" e
improvisava: mergeava com gh por fora da fila, ou perguntava ao dono o que o
nivel ja autorizava. Agora ready/ship/audit/queue add terminam com a linha
`PROXIMO PASSO:`, e o `stop` da fila diz se ha executor vivo (o lease).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from conftest_paths import CORE_LOCK, CORE_SRC


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class ConductorAnnounceTests(unittest.TestCase):
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
        self._process("pilot")
        result = self._run("feature", "Mexer")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _process(self, level: str) -> None:
        (self.sb / ".guia" / "process.json").write_text(json.dumps(
            {"delivery": {"mode": "pr"}, "autonomy": {"default": level, "ceiling": "pilot"}}), encoding="utf-8")

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, "core/src/guia.py", *args], cwd=self.sb,
                              capture_output=True, text=True, encoding="utf-8")

    def _set(self, **fields) -> None:
        path = self.sb / ".guia" / "tasks.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["tasks"][0].update(fields)
        path.write_text(json.dumps(data), encoding="utf-8")

    def _lease(self, age_seconds: float) -> None:
        lease = self.sb / ".guia" / "queue" / "executor.lease"
        lease.parent.mkdir(parents=True, exist_ok=True)
        lease.write_text(json.dumps({"pid": 4242, "host": "maquina", "heartbeat": time.time() - age_seconds}),
                         encoding="utf-8")

    def _why(self) -> str:
        result = self._run("next", "D-001", "--json")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        return json.loads(result.stdout)["why"]

    def test_queued_stop_says_whether_an_executor_is_alive(self) -> None:
        self._set(status="Na fila")
        (self.sb / ".guia" / "queue.json").write_text(json.dumps({"paused": False, "items": [
            {"id": "D-001", "pr": 1, "state": "waiting", "approval": {"by": "autonomy"}}]}), encoding="utf-8")
        self.assertIn("sem executor ativo", self._why())
        self._lease(5)
        why = self._why()
        self.assertIn("executor ativo (pid 4242", why)
        self.assertIn("fim do chat", why)
        self._lease(11 * 60)
        self.assertIn("sem executor ativo", self._why(), "batimento velho = executor morto")

    def test_ready_ends_announcing_the_next_step(self) -> None:
        (self.sb / "a.txt").write_text("x", encoding="utf-8")
        result = self._run("ready", "D-001", "--file", "a.txt", "--summary", "feito")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("PROXIMO PASSO: ship", result.stdout)
        self.assertIn("Siga sem perguntar", result.stdout)
        self.assertIn("nunca `gh pr merge`", result.stdout)

    def test_manual_level_announces_the_stop(self) -> None:
        self._process("manual")
        (self.sb / "a.txt").write_text("x", encoding="utf-8")
        result = self._run("ready", "D-001", "--file", "a.txt", "--summary", "feito")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("PROXIMO PASSO: pare - nivel manual", result.stdout)
        self.assertNotIn("Siga sem perguntar", result.stdout)


if __name__ == "__main__":
    unittest.main()
