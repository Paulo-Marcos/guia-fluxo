"""D-152: o condutor - `guia next` diz o proximo passo, e o motor decide.

Depois do `ready`, o nivel conduz: manual para; pr faz ship e auditoria;
queue e pilot ainda entram na fila. O chat encerra no `queue add` - integrar,
limpar e fechar e da fila. `stop` sempre traz o motivo e quem destrava. Modo
direct e nivel manual param logo apos o ready (o comportamento de antes).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import CORE_LOCK, CORE_SRC

A, B = "a" * 40, "b" * 40


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class ConductorTests(unittest.TestCase):
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
        self._process("pr", "pilot")
        result = self._run("feature", "Mexer")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _process(self, mode: str, level: str) -> None:
        (self.sb / ".guia" / "process.json").write_text(json.dumps(
            {"delivery": {"mode": mode}, "autonomy": {"default": level, "ceiling": "pilot"}}), encoding="utf-8")

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, "core/src/guia.py", *args], cwd=self.sb,
                              capture_output=True, text=True, encoding="utf-8")

    def _set(self, **fields) -> None:
        path = self.sb / ".guia" / "tasks.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["tasks"][0].update(fields)
        path.write_text(json.dumps(data), encoding="utf-8")

    def _queue(self, approval) -> None:
        (self.sb / ".guia" / "queue.json").write_text(json.dumps({"paused": False, "items": [
            {"id": "D-001", "pr": 1, "state": "waiting", "approval": approval,
             "humanReason": None if approval else "toca caminho alwaysHuman: .github/x.yml"}]}), encoding="utf-8")

    def _next(self) -> dict:
        result = self._run("next", "D-001", "--json")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_in_development_means_implement_then_ready(self) -> None:
        self.assertEqual(self._next()["step"], "ready")

    def test_after_ready_the_level_decides(self) -> None:
        self._set(status="Aguardando validacao")
        self.assertEqual(self._next()["step"], "ship")
        self._process("pr", "manual")
        step = self._next()
        self.assertEqual((step["step"], step["owner"]), ("stop", "dono"), "manual: o ready e o fim, como antes")

    def test_direct_mode_stops_after_ready(self) -> None:
        self._process("direct", "pilot")
        self._set(status="Aguardando validacao")
        self.assertIn("modo direct", self._next()["why"])

    def test_pr_needs_an_audit_on_the_current_head(self) -> None:
        self._set(status="Em PR", pr={"number": 1, "head": B}, audit={"result": "approved", "auditedSha": A})
        self.assertEqual(self._next()["step"], "audit", "a auditoria e de outro head")
        self._set(audit={"result": "rejected", "auditedSha": B})
        self.assertEqual(self._next()["owner"], "agente", "reprovada: o agente corrige")
        self._set(audit={"result": "approved", "auditedSha": B})
        self.assertEqual(self._next()["step"], "queue-add")
        self._process("pr", "pr")
        step = self._next()
        self.assertEqual((step["step"], step["owner"]), ("stop", "dono"), "nivel pr: fila e do dono")

    def test_the_chat_ends_at_the_queue(self) -> None:
        self._set(status="Na fila")
        self._queue({"by": "autonomy"})
        step = self._next()
        self.assertEqual((step["step"], step["owner"]), ("stop", "fila"))
        self._queue(None)
        step = self._next()
        self.assertEqual(step["owner"], "dono")
        self.assertIn(".github/x.yml", step["why"])

    def test_returned_pr_goes_back_to_the_agent(self) -> None:
        self._set(status="Em desenvolvimento", queue={"returnReason": "conflito com a base"})
        step = self._next()
        self.assertEqual((step["step"], step["owner"]), ("stop", "agente"))
        self.assertIn("conflito", step["why"])

    def test_integrated_explains_why_it_did_not_close(self) -> None:
        self._set(status="Integrada", autoFinish={"checks": [
            {"check": "tipo permitido", "ok": False, "evidence": "feature fora de [chore]"},
            {"check": "main verde", "ok": True, "evidence": "pass"}]})
        step = self._next()
        self.assertEqual(step["owner"], "dono")
        self.assertIn("tipo permitido", step["why"])
        self.assertNotIn("main verde", step["why"])

    def test_ready_body_hands_over_to_the_conductor(self) -> None:
        from conftest_paths import REPO_ROOT

        body = (REPO_ROOT / "plugins" / "guia" / "commands" / "ready.md").read_text(encoding="utf-8")
        self.assertIn("next <D-NNN> --json", body)
        for rule in ("Never run `finish`", "queue run", "[unlock:]"):
            self.assertIn(rule, body)


if __name__ == "__main__":
    unittest.main()
