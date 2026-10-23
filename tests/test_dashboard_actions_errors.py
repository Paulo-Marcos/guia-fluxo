"""D-196: erros das acoes do painel e a regra unica de fila parada.

O motor que falha devolve 500 com a propria saida; o projeto do cadastro que
perdeu o `.guia/tasks.json` devolve 404; o retrato expoe `stopped` (pausada ou
congelada), a regra que o servidor usa e que a pagina repete.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from conftest_paths import ensure_core_importable

ensure_core_importable()

import _dashboard  # noqa: E402
import _dashboard_actions  # noqa: E402
from _dashboard_page import PAGE_HTML  # noqa: E402
from test_dashboard_actions import _project, _Server  # noqa: E402
from test_dashboard_scroll import DOM_STUB  # noqa: E402


class EngineFailureTests(_Server):
    def test_resume_that_fails_returns_500_with_the_engine_output(self) -> None:
        root = self.add(_project(self.tmp / "app", queue={"items": [], "paused": True}))
        failed = subprocess.CompletedProcess(args=[], returncode=1, stdout="saida do motor\n", stderr="fila travada\n")
        with mock.patch.object(_dashboard_actions.subprocess, "run", return_value=failed) as run:
            status, body = self.post("queue-resume", root)
        self.assertEqual(status, 500)
        self.assertIn("saida do motor", body["message"])
        self.assertIn("fila travada", body["message"])
        self.assertEqual(run.call_args.args[0][-2:], ["queue", "resume"])
        self.assertTrue(self.queue_doc(root)["paused"])

    def test_silent_failure_still_says_the_exit_code(self) -> None:
        root = self.add(_project(self.tmp / "app", queue={"items": [], "paused": True}))
        failed = subprocess.CompletedProcess(args=[], returncode=3, stdout="", stderr="")
        with mock.patch.object(_dashboard_actions.subprocess, "run", return_value=failed):
            status, body = self.post("queue-resume", root)
        self.assertEqual(status, 500)
        self.assertIn("3", body["message"])


class LostProjectTests(_Server):
    def test_registered_project_without_tasks_json_returns_404(self) -> None:
        root = self.add(_project(self.tmp / "app", queue={"items": [], "paused": True}))
        (root / ".guia" / "tasks.json").unlink()
        with mock.patch.object(_dashboard_actions.subprocess, "run") as run:
            status, body = self.post("queue-resume", root)
        self.assertEqual(status, 404)
        self.assertIn("tasks.json", body["message"])
        run.assert_not_called()


class StoppedFieldTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def stopped(self, name: str, queue: dict) -> bool:
        return _dashboard.snapshot(_project(self.tmp / name, queue=queue))["queue"]["stopped"]

    def test_paused_or_frozen_is_stopped(self) -> None:
        self.assertTrue(self.stopped("paused", {"items": [], "paused": True}))
        self.assertTrue(self.stopped("frozen", {"items": [], "frozenReason": "main vermelha"}))
        self.assertFalse(self.stopped("open", {"items": []}))

    def test_start_executor_refuses_a_frozen_queue(self) -> None:
        root = _project(self.tmp / "frozen", queue={"items": [], "frozenReason": "main vermelha"})
        with mock.patch.object(_dashboard_actions.subprocess, "Popen") as popen:
            with self.assertRaises(_dashboard_actions.ActionError) as caught:
                _dashboard_actions.start_executor(root)
        self.assertEqual(caught.exception.status, 409)
        popen.assert_not_called()


ACTION_PROBE = r"""
(async () => {
  const out = [];
  for (const queue of QUEUES) {
    snapshot = JSON.parse(JSON.stringify(BASE));
    Object.assign(snapshot.projects[0].queue, queue);
    await refresh();
    out.push(document.querySelectorAll(".btn").map(b => b.textContent));
  }
  console.log(JSON.stringify(out));
})();
"""


@unittest.skipUnless(shutil.which("node"), "node ausente")
class PageAgreesWithStoppedTest(unittest.TestCase):
    def test_retomar_shows_exactly_when_the_snapshot_says_stopped(self) -> None:
        """A pagina ainda repete a regra (teste travado da D-195 monta o retrato
        sem `stopped`); este teste garante que as duas copias nao divergem."""
        queues = [{"paused": True}, {"frozenReason": "main vermelha"}, {}]
        for queue in queues:
            queue["stopped"] = _dashboard.queue_stopped(queue)
        stages = [{"label": f"Etapa {i}", "cards": []} for i in range(8)]
        base = {"guia": {"version": "9.9.9", "engine": "x"}, "projects": [{
            "name": "p", "path": "C:\\p", "mode": "pr", "active": 0, "current": None, "stages": stages,
            "doneTotal": 0, "recentDone": [],
            "queue": {"items": [], "history": [], "executor": None, "head": None},
        }]}
        script = re.search(r"<script>(.*?)</script>", PAGE_HTML, re.S).group(1)
        probe = ACTION_PROBE.replace("QUEUES", json.dumps(queues)).replace("BASE", json.dumps(base))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "probe.js"
            path.write_text(DOM_STUB + script + probe, encoding="utf-8")
            out = subprocess.run(["node", str(path)], capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(out.returncode, 0, out.stderr)
        got = json.loads(out.stdout.strip().splitlines()[-1])
        expected = [["Retomar fila"] if q["stopped"] else ["Iniciar executor"] for q in queues]
        self.assertEqual(got, expected)


if __name__ == "__main__":
    unittest.main()
