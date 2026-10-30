"""D-203: `painel` liga a fila e abre o painel sem sessao de IA.

Reaproveita o `start_executor` do botao (D-187): o que o painel recusaria
(executor vivo, fila parada) vira aviso; um painel ja aberto e reaproveitado.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from conftest_paths import ensure_core_importable

ensure_core_importable()

import _cli_dashboard  # noqa: E402
import _cli_painel  # noqa: E402
from _dashboard_actions import ActionError  # noqa: E402


def _project(root: Path) -> Path:
    (root / ".guia").mkdir(parents=True)
    (root / ".guia" / "tasks.json").write_text(json.dumps({"schemaVersion": 1, "tasks": []}), encoding="utf-8")
    (root / ".guia" / "process.json").write_text(json.dumps({"delivery": {"mode": "pr"}}), encoding="utf-8")
    return root


def _args(**overrides: object) -> argparse.Namespace:
    base = {"sem_fila": False, "atalho": False, "port": 18990, "no_open": True}
    base.update(overrides)
    return argparse.Namespace(**base)


class _Base(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.root = _project(self.tmp / "proj")
        for patcher in (
            mock.patch.dict(os.environ, {"GUIA_HOME": str(self.tmp / "home")}),
            mock.patch.object(_cli_painel, "ROOT", self.root),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_painel(self, **overrides: object) -> tuple[int, str]:
        out = io.StringIO()
        with redirect_stdout(out):
            code = _cli_painel.cmd_painel(_args(**overrides))
        return code, out.getvalue()


class EnsureQueueTests(_Base):
    def test_starts_the_executor_through_the_dashboard_action(self) -> None:
        with mock.patch.object(_cli_painel, "start_executor", return_value="Executor iniciado (pid 7).") as start:
            self.assertEqual(_cli_painel.ensure_queue(self.root), "FILA: Executor iniciado (pid 7).")
        start.assert_called_once_with(self.root)

    def test_live_executor_is_only_a_warning(self) -> None:
        refusal = ActionError(409, "executor ja ativo (pid 9 em pc)")
        with mock.patch.object(_cli_painel, "start_executor", side_effect=refusal):
            self.assertEqual(_cli_painel.ensure_queue(self.root), "FILA: executor ja ativo (pid 9 em pc)")


class RunningDashboardTests(unittest.TestCase):
    def test_finds_an_open_dashboard(self) -> None:
        server = _cli_dashboard._bind(18960)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        port = server.server_address[1]
        self.assertEqual(_cli_painel.running_dashboard(port), f"http://127.0.0.1:{port}/")

    def test_none_when_nothing_listens(self) -> None:
        with mock.patch.object(_cli_painel, "_PORT_TRIES", 1):
            self.assertIsNone(_cli_painel.running_dashboard(18999))


class CmdPainelTests(_Base):
    def test_reuses_open_dashboard_after_starting_the_queue(self) -> None:
        with mock.patch.object(_cli_painel, "ensure_queue", return_value="FILA: ok") as queue, \
                mock.patch.object(_cli_painel, "running_dashboard", return_value="http://127.0.0.1:8765/"), \
                mock.patch.object(_cli_painel, "_serve") as serve:
            code, out = self.run_painel()
        self.assertEqual(code, 0)
        queue.assert_called_once_with(self.root)
        serve.assert_not_called()
        self.assertIn("FILA: ok", out)
        self.assertIn("PAINEL: http://127.0.0.1:8765/ (ja aberto)", out)

    def test_serves_when_no_dashboard_and_skips_queue_on_request(self) -> None:
        with mock.patch.object(_cli_painel, "ensure_queue") as queue, \
                mock.patch.object(_cli_painel, "running_dashboard", return_value=None), \
                mock.patch.object(_cli_painel, "_serve", return_value=0) as serve:
            code, _ = self.run_painel(sem_fila=True)
        self.assertEqual(code, 0)
        queue.assert_not_called()
        serve.assert_called_once()

    def test_refuses_outside_a_project(self) -> None:
        with mock.patch.object(_cli_painel, "ROOT", self.tmp / "vazio"), self.assertRaises(SystemExit):
            self.run_painel()


class ShortcutTests(_Base):
    def test_shortcut_runs_painel_in_the_project(self) -> None:
        done = mock.Mock(returncode=0, stdout="C:\\Desk\\Guia - proj.lnk\r\nC:\\Start\\Guia - proj.lnk\r\n", stderr="")
        with mock.patch.object(_cli_painel.os, "name", "nt"), \
                mock.patch.object(_cli_painel.subprocess, "run", return_value=done) as run:
            code, out = self.run_painel(atalho=True)
        self.assertEqual(code, 0)
        env = run.call_args.kwargs["env"]
        self.assertEqual(env["GUIA_LNK_NAME"], "Guia - proj.lnk")
        self.assertEqual(env["GUIA_LNK_DIR"], str(self.root))
        self.assertTrue(env["GUIA_LNK_ARGS"].endswith('" painel'))
        self.assertIn("Atalho: C:\\Desk\\Guia - proj.lnk", out)
        self.assertIn("/plugin update", out)

    def test_shortcut_is_windows_only(self) -> None:
        with mock.patch.object(_cli_painel.os, "name", "posix"), self.assertRaises(SystemExit):
            _cli_painel.create_shortcut(self.root)


if __name__ == "__main__":
    unittest.main()
