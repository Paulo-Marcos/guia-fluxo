"""D-175: painel local - retrato dos projetos, fila, executor e cadastro."""

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


def _project(root: Path, tasks: list[dict], queue: dict | None = None, lease: dict | None = None) -> Path:
    guia = root / ".guia"
    guia.mkdir(parents=True)
    (guia / "tasks.json").write_text(json.dumps({"schemaVersion": 1, "tasks": tasks}), encoding="utf-8")
    (guia / "process.json").write_text(json.dumps({"projectName": root.name, "delivery": {"mode": "pr"}}), encoding="utf-8")
    if queue is not None:
        (guia / "queue.json").write_text(json.dumps(queue), encoding="utf-8")
    if lease is not None:
        (guia / "queue").mkdir()
        (guia / "queue" / "executor.lease").write_text(json.dumps(lease), encoding="utf-8")
    return root


def _task(task_id: str, status: str, **extra) -> dict:
    return {"id": task_id, "kind": "feature", "title": f"titulo {task_id}", "status": status, "updatedAt": "2026-10-15", **extra}


def _item(task_id: str, enqueued: str, **extra) -> dict:
    return {"id": task_id, "state": "waiting", "priority": "normal", "enqueuedAt": enqueued, "dependsOn": [],
            "auditedSha": "abc", "approval": {"by": "user"}, "pr": 1, **extra}


class SnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def test_demands_grouped_by_stage_and_done_apart(self) -> None:
        root = _project(self.tmp / "app", [
            _task("D-001", "Em desenvolvimento"),
            _task("D-002", "Aguardando validação"),
            _task("D-003", "Na fila"),
            _task("D-004", "Validada", finishedAt="2026-10-14"),
            _task("D-005", "Bloqueada", blocks=[{"reason": "esperando API"}]),
        ])
        snap = _dashboard.snapshot(root)
        self.assertEqual(snap["counts"]["Em desenvolvimento"], 1)
        self.assertEqual(snap["counts"]["Aguardando validacao"], 1)  # acento normalizado
        self.assertEqual(snap["counts"]["Na fila"], 1)
        self.assertEqual([c["id"] for c in snap["recentDone"]], ["D-004"])
        blocked = next(s for s in snap["stages"] if s["key"] == "Bloqueada")["cards"][0]
        self.assertEqual(blocked["blockedReason"], "esperando API")

    def test_queue_order_head_and_next_to_integrate(self) -> None:
        queue = {"items": [
            _item("D-002", "2026-10-15T10:00:00"),
            _item("D-001", "2026-10-15T09:00:00", state="conflict", conflictReason="CI vermelho"),
            _item("D-003", "2026-10-15T11:00:00", priority="hotfix", approval=None),
        ]}
        root = _project(self.tmp / "app", [_task(i, "Na fila") for i in ("D-001", "D-002", "D-003")], queue)
        q = _dashboard.snapshot(root)["queue"]
        self.assertEqual([i["id"] for i in q["items"]], ["D-003", "D-001", "D-002"])  # hotfix na frente
        self.assertEqual(q["head"]["id"], "D-003")
        self.assertIn("aprovacao", q["head"]["waiting"])
        self.assertEqual(q["next"]["id"], "D-002")  # o primeiro elegivel, nao a ponta
        self.assertEqual([i["id"] for i in q["items"] if i["next"]], ["D-002"])

    def test_executor_alive_stale_and_absent(self) -> None:
        alive = _project(self.tmp / "a", [], {"items": []}, {"pid": 7, "host": "pc", "heartbeat": time.time() - 5})
        stale = _project(self.tmp / "b", [], {"items": []}, {"pid": 8, "host": "pc", "heartbeat": time.time() - 3600})
        none = _project(self.tmp / "c", [])
        self.assertTrue(_dashboard.snapshot(alive)["queue"]["executor"]["alive"])
        self.assertFalse(_dashboard.snapshot(stale)["queue"]["executor"]["alive"])
        self.assertIsNone(_dashboard.snapshot(none)["queue"]["executor"])

    def test_overview_survives_missing_project(self) -> None:
        good = _project(self.tmp / "ok", [_task("D-001", "Backlog")])
        data = _dashboard.overview([str(good), str(self.tmp / "sumiu")])
        self.assertNotIn("error", data["projects"][0])
        self.assertIn("error", data["projects"][1])


class RegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        patcher = mock.patch.dict(os.environ, {"GUIA_HOME": str(self.tmp / "home")})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_scan_finds_projects_and_skips_worktrees(self) -> None:
        _project(self.tmp / "dev" / "um", [])
        _project(self.tmp / "dev" / "grupo" / "dois", [])
        worktree = self.tmp / "dev" / "um-d001" / ".guia"
        worktree.mkdir(parents=True)
        (worktree / "process.json").write_text("{}", encoding="utf-8")  # worktree: so config
        found = sorted(p.name for p in _dashboard.scan(self.tmp / "dev"))
        self.assertEqual(found, ["dois", "um"])

    def test_add_is_idempotent_and_remove(self) -> None:
        root = _project(self.tmp / "app", [])
        self.assertEqual(len(_dashboard.add_projects([root])), 1)
        self.assertEqual(_dashboard.add_projects([root]), [])
        self.assertEqual(len(_dashboard.load_projects()), 1)
        self.assertTrue(_dashboard.remove_project(root))
        self.assertEqual(_dashboard.load_projects(), [])

    def test_add_ignores_folder_without_guia(self) -> None:
        (self.tmp / "vazio").mkdir()
        self.assertEqual(_dashboard.add_projects([self.tmp / "vazio"]), [])


class ServerTests(unittest.TestCase):
    def setUp(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        patcher = mock.patch.dict(os.environ, {"GUIA_HOME": str(tmp / "home")})
        patcher.start()
        self.addCleanup(patcher.stop)
        _dashboard.add_projects([_project(tmp / "app", [_task("D-001", "Em desenvolvimento")])])
        self.server = _cli_dashboard._bind(18765)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def _get(self, path: str, host: str | None = None) -> tuple[int, bytes]:
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}")
        if host:
            request.add_header("Host", host)
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read()

    def test_serves_page_and_snapshot(self) -> None:
        status, body = self._get("/")
        self.assertEqual(status, 200)
        self.assertIn(b"Guia Fluxo", body)
        status, body = self._get("/api/snapshot")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["projects"][0]["counts"]["Em desenvolvimento"], 1)

    def test_rejects_foreign_host_header(self) -> None:
        status, _ = self._get("/api/snapshot", host="evil.example:80")
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()
