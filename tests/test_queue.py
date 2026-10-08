"""D-126: a fila de integracao (R5) - estado atomico, ordem e aprovacao.

`.guia/queue.json` e escrito por varios chats ao mesmo tempo: toda escrita
passa por uma trava de arquivo (`O_EXCL`) e grava em temporario + `os.replace`.
A ordem e FIFO com `hotfix` a frente; dependencia aberta ou falta de
aprovacao fazem o item esperar sem bloquear os de tras. `queue add` exige PR
aberto, auditoria aprovada no head atual e a mensagem de squash.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import CORE_LOCK, CORE_SRC, ensure_core_importable

ensure_core_importable()

import _merge_queue as _queue  # noqa: E402

HEAD = "a" * 40


class QueueOrderTests(unittest.TestCase):
    def _item(self, task_id: str, at: str, **extra) -> dict:
        return {"id": task_id, "state": "waiting", "priority": "normal", "enqueuedAt": at,
                "approval": {"by": "user"}, "dependsOn": [], **extra}

    def test_fifo_hotfix_first_and_waits_do_not_block(self) -> None:
        items = [
            self._item("D-1", "2026-10-08T10:00:00"),
            self._item("D-2", "2026-10-08T10:01:00", approval=None),
            self._item("D-3", "2026-10-08T10:02:00", dependsOn=["D-9"]),
            self._item("D-4", "2026-10-08T10:03:00", priority="hotfix"),
            self._item("D-5", "2026-10-08T10:04:00"),
        ]
        statuses = {"D-9": "Em desenvolvimento"}
        order = _queue.ordered(items, lambda task_id: statuses.get(task_id))
        self.assertEqual([i["id"] for i, why in order if why is None], ["D-4", "D-1", "D-5"])
        reasons = {i["id"]: why for i, why in order if why}
        self.assertIn("aprov", reasons["D-2"])
        self.assertIn("D-9", reasons["D-3"])


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class QueueCliTests(unittest.TestCase):
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
        (self.sb / ".guia" / "process.json").write_text(json.dumps({"delivery": {"mode": "pr"}}), encoding="utf-8")
        for title in ("primeira", "segunda"):
            self._ok("feature", title)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "core/src/guia.py", *args],
            cwd=self.sb, capture_output=True, text=True, encoding="utf-8",
        )

    def _ok(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = self._run(*args)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def _shipped(self, task_id: str, audited: str | None = HEAD) -> None:
        """Estado sintetico de demanda ja em PR (o que ship + audit gravariam)."""
        path = self.sb / ".guia" / "tasks.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for task in data["tasks"]:
            if task["id"] == task_id:
                task["status"] = "Em PR"
                task["pr"] = {"number": int(task_id[2:]), "url": "u", "branch": f"b-{task_id}", "head": HEAD}
                if audited:
                    task["audit"] = {"result": "approved", "auditedSha": audited, "auditedPatchId": "p"}
        path.write_text(json.dumps(data), encoding="utf-8")
        (self.sb / ".guia" / "queue").mkdir(exist_ok=True)
        (self.sb / ".guia" / "queue" / f"{task_id}.msg").write_text("msg\n", encoding="utf-8")

    def _status(self, task_id: str) -> str:
        tasks = json.loads((self.sb / ".guia" / "tasks.json").read_text(encoding="utf-8"))["tasks"]
        return next(t["status"] for t in tasks if t["id"] == task_id)

    def _queue(self) -> dict:
        return json.loads((self.sb / ".guia" / "queue.json").read_text(encoding="utf-8"))

    def test_add_requires_approved_audit_on_the_current_head(self) -> None:
        self._shipped("D-001", audited=None)
        self.assertNotEqual(self._run("queue", "add", "D-001").returncode, 0)
        self._shipped("D-001", audited="b" * 40)
        result = self._run("queue", "add", "D-001")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("head", result.stdout + result.stderr)
        self._shipped("D-001")
        self._ok("queue", "add", "D-001")
        item = self._queue()["items"][0]
        self.assertEqual((item["id"], item["pr"], item["auditedSha"], item["state"]), ("D-001", 1, HEAD, "waiting"))
        self.assertEqual(self._status("D-001"), "Na fila")

    def test_list_explains_why_items_wait_and_approve_releases(self) -> None:
        self._shipped("D-001")
        self._shipped("D-002")
        self._ok("queue", "add", "D-001")
        self._ok("queue", "add", "D-002", "--priority", "hotfix")
        listing = json.loads(self._ok("queue", "--json").stdout)
        self.assertEqual([i["id"] for i in listing["items"]], ["D-002", "D-001"])
        self.assertTrue(all("aprov" in i["waiting"] for i in listing["items"]))
        self._ok("approve", "--all")
        listing = json.loads(self._ok("queue", "--json").stdout)
        self.assertEqual([i["waiting"] for i in listing["items"]], [None, None])
        self.assertEqual(self._queue()["items"][0]["approval"]["by"], "user")

    def test_remove_pause_and_priority(self) -> None:
        self._shipped("D-001")
        self._ok("queue", "add", "D-001")
        self._ok("queue", "priority", "D-001", "hotfix")
        self.assertEqual(self._queue()["items"][0]["priority"], "hotfix")
        self._ok("queue", "pause", "--reason", "main em manutencao")
        self.assertTrue(self._queue()["paused"])
        self.assertIn("main em manutencao", self._ok("queue").stdout)
        self._ok("queue", "resume")
        self.assertFalse(self._queue()["paused"])
        self._ok("queue", "remove", "D-001")
        self.assertEqual(self._queue()["items"], [])
        self.assertEqual(self._status("D-001"), "Em PR")

    def test_twenty_parallel_writers_keep_every_item(self) -> None:
        script = (
            "import sys; sys.path.insert(0, 'core/src');"
            "import _merge_queue as _queue;"
            "n = sys.argv[1];"
            "_queue.mutate(lambda q: q['items'].append({'id': 'X-' + n}))"
        )
        procs = [
            subprocess.Popen([sys.executable, "-c", script, str(n)], cwd=self.sb,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            for n in range(20)
        ]
        for proc in procs:
            _out, err = proc.communicate(timeout=120)
            self.assertEqual(proc.returncode, 0, msg=err.decode("utf-8", "replace"))
        ids = sorted(item["id"] for item in self._queue()["items"])
        self.assertEqual(ids, sorted(f"X-{n}" for n in range(20)))
        self.assertFalse((self.sb / ".guia" / "queue.lock").exists(), "trava liberada no fim")


if __name__ == "__main__":
    unittest.main()
