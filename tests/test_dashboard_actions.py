"""D-187: botoes do painel - retomar a fila e iniciar o executor.

O servidor so aceita escrita com Host local, Origin do painel, corpo JSON e o
token da sessao; a acao roda o motor dentro do projeto e nunca abre um
segundo executor.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

from conftest_paths import ensure_core_importable

ensure_core_importable()

import _cli_dashboard  # noqa: E402
import _dashboard  # noqa: E402
import _dashboard_actions  # noqa: E402
from _dashboard_page import TOKEN_PLACEHOLDER  # noqa: E402


def _project(root: Path, queue: dict | None = None, lease: dict | None = None, mode: str = "pr") -> Path:
    guia = root / ".guia"
    guia.mkdir(parents=True)
    (guia / "tasks.json").write_text(json.dumps({"schemaVersion": 1, "tasks": []}), encoding="utf-8")
    (guia / "process.json").write_text(json.dumps({"projectName": root.name, "delivery": {"mode": mode}}), encoding="utf-8")
    (guia / "queue.json").write_text(json.dumps(queue or {"items": []}), encoding="utf-8")
    if lease is not None:
        (guia / "queue").mkdir()
        (guia / "queue" / "executor.lease").write_text(json.dumps(lease), encoding="utf-8")
    return root


class _Server(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        patcher = mock.patch.dict(os.environ, {"GUIA_HOME": str(self.tmp / "home")})
        patcher.start()
        self.addCleanup(patcher.stop)
        _dashboard_actions._spawned.clear()
        self.server = _cli_dashboard._bind(18850)
        self.port = self.server.server_address[1]
        self.token = self.server.guia_token
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def add(self, root: Path) -> Path:
        _dashboard.add_projects([root])
        return root

    def post(self, action: str, project: Path | str, headers: dict[str, str] | None = None,
             body: bytes | None = None) -> tuple[int, dict]:
        base = {
            "Content-Type": "application/json",
            "Origin": f"http://127.0.0.1:{self.port}",
            "X-Guia-Token": self.token,
        }
        base.update(headers or {})
        data = body if body is not None else json.dumps({"project": str(project)}).encode("utf-8")
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}/api/action/{action}", data=data, method="POST")
        for name, value in base.items():
            if value is not None:
                request.add_header(name, value)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read() or b"{}")

    def queue_doc(self, root: Path) -> dict:
        return json.loads((root / ".guia" / "queue.json").read_text(encoding="utf-8"))


class RejectedRequestTests(_Server):
    """Nenhum pedido recusado chega a mexer na fila."""

    def setUp(self) -> None:
        super().setUp()
        self.root = self.add(_project(self.tmp / "app", queue={"items": [], "paused": True, "pausedReason": "manutencao"}))

    def assert_refused(self, status: int, expected: int) -> None:
        self.assertEqual(status, expected)
        self.assertTrue(self.queue_doc(self.root)["paused"])

    def test_without_token(self) -> None:
        status, body = self.post("queue-resume", self.root, {"X-Guia-Token": None})
        self.assert_refused(status, 403)
        self.assertIn("token", body["message"])

    def test_wrong_token(self) -> None:
        status, _ = self.post("queue-resume", self.root, {"X-Guia-Token": "x" * 43})
        self.assert_refused(status, 403)

    def test_foreign_origin(self) -> None:
        status, body = self.post("queue-resume", self.root, {"Origin": "http://evil.example"})
        self.assert_refused(status, 403)
        self.assertIn("origem", body["message"])

    def test_missing_origin(self) -> None:
        status, _ = self.post("queue-resume", self.root, {"Origin": None})
        self.assert_refused(status, 403)

    def test_origin_on_another_local_port(self) -> None:
        status, _ = self.post("queue-resume", self.root, {"Origin": f"http://127.0.0.1:{self.port + 1}"})
        self.assert_refused(status, 403)

    def test_foreign_host(self) -> None:
        status, _ = self.post("queue-resume", self.root, {"Host": "evil.example"})
        self.assert_refused(status, 403)

    def test_simple_form_content_type(self) -> None:
        status, _ = self.post("queue-resume", self.root, {"Content-Type": "text/plain"})
        self.assert_refused(status, 415)

    def test_project_outside_the_registry(self) -> None:
        other = _project(self.tmp / "fora", queue={"items": [], "paused": True})
        status, _ = self.post("queue-resume", other)
        self.assertEqual(status, 404)
        self.assertTrue(self.queue_doc(other)["paused"])

    def test_unknown_action(self) -> None:
        status, _ = self.post("queue-pause", self.root)
        self.assertEqual(status, 404)

    def test_get_does_not_act(self) -> None:
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}/api/action/queue-resume")
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request, timeout=5)
        self.assertEqual(caught.exception.code, 404)
        self.assertTrue(self.queue_doc(self.root)["paused"])


class PageTokenTests(_Server):
    def test_page_carries_this_session_token_and_refuses_framing(self) -> None:
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/", timeout=5) as response:
            page = response.read().decode("utf-8")
            self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertIn(f'content="{self.token}"', page)
        self.assertNotIn(TOKEN_PLACEHOLDER, page)

    def test_each_dashboard_session_has_its_own_token(self) -> None:
        other = _cli_dashboard._bind(self.port + 1)
        self.addCleanup(other.server_close)
        self.assertNotEqual(other.guia_token, self.token)


class ResumeTests(_Server):
    def test_resume_runs_the_engine_in_the_project(self) -> None:
        root = self.add(_project(self.tmp / "app", queue={"items": [], "paused": True, "pausedReason": "manutencao"}))
        status, body = self.post("queue-resume", root)
        self.assertEqual(status, 200, body)
        self.assertIn("retomada", body["message"])
        self.assertFalse(self.queue_doc(root)["paused"])

    def test_resume_refused_when_not_paused(self) -> None:
        root = self.add(_project(self.tmp / "app"))
        status, _ = self.post("queue-resume", root)
        self.assertEqual(status, 409)


class StartExecutorTests(_Server):
    def popen(self) -> mock.MagicMock:
        patcher = mock.patch.object(_dashboard_actions.subprocess, "Popen")
        fake = patcher.start()
        self.addCleanup(patcher.stop)
        fake.return_value.pid = 4242
        fake.return_value.poll.return_value = None  # ainda rodando
        return fake

    def test_starts_queue_run_detached_in_the_project(self) -> None:
        fake = self.popen()
        root = self.add(_project(self.tmp / "app"))
        status, body = self.post("queue-run", root)
        self.assertEqual(status, 200, body)
        self.assertIn("4242", body["message"])
        args, kwargs = fake.call_args
        self.assertEqual(args[0][-2:], ["queue", "run"])
        self.assertEqual(Path(kwargs["env"]["GUIA_PROJECT_ROOT"]), root)
        self.assertEqual(Path(kwargs["cwd"]), root)
        self.assertTrue(kwargs.get("creationflags") or kwargs.get("start_new_session"))
        self.assertTrue((root / ".guia" / "queue" / "executor-painel.log").is_file())

    def test_refused_while_an_executor_is_alive(self) -> None:
        fake = self.popen()
        lease = {"pid": 77, "host": "maquina", "heartbeat": time.time()}
        root = self.add(_project(self.tmp / "app", lease=lease))
        status, body = self.post("queue-run", root)
        self.assertEqual(status, 409)
        self.assertIn("pid 77", body["message"])
        fake.assert_not_called()

    def test_stale_lease_does_not_block(self) -> None:
        self.popen()
        lease = {"pid": 77, "host": "maquina", "heartbeat": time.time() - 3600}
        root = self.add(_project(self.tmp / "app", lease=lease))
        status, _ = self.post("queue-run", root)
        self.assertEqual(status, 200)

    def test_second_click_before_the_lease_does_not_start_another(self) -> None:
        fake = self.popen()
        root = self.add(_project(self.tmp / "app"))
        self.assertEqual(self.post("queue-run", root)[0], 200)
        status, _ = self.post("queue-run", root)
        self.assertEqual(status, 409)
        self.assertEqual(fake.call_count, 1)

    def test_concurrent_clicks_start_one_executor(self) -> None:
        fake = self.popen()
        root = self.add(_project(self.tmp / "app"))
        results: list[int] = []
        threads = [threading.Thread(target=lambda: results.append(self.post("queue-run", root)[0])) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(sorted(results), [200, 409, 409, 409, 409])
        self.assertEqual(fake.call_count, 1)

    def test_refused_while_queue_is_paused(self) -> None:
        fake = self.popen()
        root = self.add(_project(self.tmp / "app", queue={"items": [], "paused": True}))
        status, _ = self.post("queue-run", root)
        self.assertEqual(status, 409)
        fake.assert_not_called()

    def test_refused_without_pr_delivery(self) -> None:
        fake = self.popen()
        root = self.add(_project(self.tmp / "app", mode="direct"))
        status, _ = self.post("queue-run", root)
        self.assertEqual(status, 409)
        fake.assert_not_called()


if __name__ == "__main__":
    unittest.main()
