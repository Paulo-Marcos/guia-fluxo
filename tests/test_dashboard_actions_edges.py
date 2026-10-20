"""D-187: bordas dos botoes do painel, achadas na auditoria do PR #85.

Corpo malformado, Origin `localhost`, fila congelada, motor escolhido pelo
projeto e o executor sem janela de console no Windows.
"""

from __future__ import annotations

import http.client
import json
import os
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from conftest_paths import ensure_core_importable

ensure_core_importable()

import _dashboard_actions  # noqa: E402
from test_dashboard_actions import _project, _Server  # noqa: E402


class MalformedBodyTests(_Server):
    def setUp(self) -> None:
        super().setUp()
        self.root = self.add(_project(self.tmp / "app", queue={"items": [], "paused": True}))

    def raw_post(self, body: bytes, length: str | None) -> int:
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        self.addCleanup(conn.close)
        conn.putrequest("POST", "/api/action/queue-resume")
        conn.putheader("Content-Type", "application/json")
        conn.putheader("Origin", f"http://127.0.0.1:{self.port}")
        conn.putheader("X-Guia-Token", self.token)
        if length is not None:
            conn.putheader("Content-Length", length)
        conn.endheaders(body)
        return conn.getresponse().status

    def test_missing_negative_or_huge_length(self) -> None:
        self.assertEqual(self.raw_post(b"", None), 400)
        self.assertEqual(self.raw_post(b"", "-5"), 400)
        self.assertEqual(self.raw_post(b"", "5000"), 400)
        self.assertTrue(self.queue_doc(self.root)["paused"])

    def test_body_that_is_not_json(self) -> None:
        status, body = self.post("queue-resume", self.root, body=b"{nao e json")
        self.assertEqual(status, 400)
        self.assertIn("JSON", body["message"])

    def test_project_that_is_not_text(self) -> None:
        status, _ = self.post("queue-resume", self.root, body=json.dumps({"project": ["x"]}).encode())
        self.assertEqual(status, 400)
        self.assertTrue(self.queue_doc(self.root)["paused"])

    def test_error_inside_the_action_is_not_reported_as_bad_json(self) -> None:
        with mock.patch.object(_dashboard_actions, "snapshot", side_effect=ValueError("quebrou")):
            status, body = self.post("queue-resume", self.root)
        self.assertEqual(status, 500)
        self.assertIn("quebrou", body["message"])


class AcceptedVariantsTests(_Server):
    def test_localhost_origin_is_the_panel_too(self) -> None:
        root = self.add(_project(self.tmp / "app", queue={"items": [], "paused": True}))
        status, _ = self.post("queue-resume", root, {"Origin": f"http://localhost:{self.port}", "Host": f"localhost:{self.port}"})
        self.assertEqual(status, 200)
        self.assertFalse(self.queue_doc(root)["paused"])

    def test_resume_thaws_a_frozen_queue(self) -> None:
        root = self.add(_project(self.tmp / "app", queue={"items": [], "paused": False, "frozenReason": "main vermelha"}))
        status, body = self.post("queue-resume", root)
        self.assertEqual(status, 200, body)
        self.assertIsNone(self.queue_doc(root).get("frozenReason"))


class EngineChoiceTests(unittest.TestCase):
    def test_project_engine_wins_over_the_dashboard_one(self) -> None:
        root = Path(self.id().replace(".", "_"))
        with mock.patch.object(Path, "is_file", lambda p: p.as_posix().endswith("plugins/guia/bin/guia.py")):
            self.assertEqual(_dashboard_actions.engine_for(root), root / "plugins/guia/bin/guia.py")

    def test_without_project_engine_uses_the_dashboard_one(self) -> None:
        with mock.patch.object(Path, "is_file", lambda p: False):
            self.assertEqual(_dashboard_actions.engine_for(Path("x")), _dashboard_actions.ENGINE)


@unittest.skipUnless(os.name == "nt", "flags de processo do Windows")
class WindowsDetachTests(unittest.TestCase):
    def test_executor_gets_a_hidden_console_not_none(self) -> None:
        flags = _dashboard_actions._detach_kwargs()["creationflags"]
        self.assertTrue(flags & subprocess.CREATE_NO_WINDOW)
        self.assertTrue(flags & subprocess.CREATE_NEW_PROCESS_GROUP)
        self.assertFalse(flags & subprocess.DETACHED_PROCESS)


if __name__ == "__main__":
    unittest.main()
