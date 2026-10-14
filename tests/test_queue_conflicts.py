"""D-164: com `delivery.queue.conflicts = manager`, o conflito fica na fila para o gerente.

Conflito com a base, rebase que conflita ou PR que mudou depois da auditoria
nao volta mais ao autor: o item fica em `conflict`, com o motivo, e o executor
segue para os outros. Resolvido pelo gerente, `queue add` o devolve a espera
no mesmo lugar, sem duplicar. Sem a chave (padrao `return`), nada muda.
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

A, B = "a" * 40, "b" * 40


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class QueueConflictTests(unittest.TestCase):
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
        (self.sb / ".guia" / "process.json").write_text(
            json.dumps({"delivery": {"mode": "pr", "queue": {"conflicts": "manager"}}}), encoding="utf-8")
        self.fixture = self.sb / "gh.json"
        self.fixture.write_text(json.dumps({"__auth__": True}), encoding="utf-8")
        self.prs: list[dict] = []
        for title in ("primeira", "segunda"):
            self._ok("feature", title)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, "core/src/guia.py", *args], cwd=self.sb, capture_output=True,
                              text=True, encoding="utf-8", env={**os.environ, "GUIA_GH_FIXTURE": str(self.fixture)})

    def _ok(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = self._run(*args)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def _audit(self, task_id: str, number: int, head: str, patch: str) -> None:
        path = self.sb / ".guia" / "tasks.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for task in data["tasks"]:
            if task["id"] == task_id:
                task["status"] = "Em PR"
                task["pr"] = {"number": number, "url": "u", "branch": f"b{number}", "head": head}
                task["audit"] = {"result": "approved", "auditedSha": head, "auditedPatchId": patch}
        path.write_text(json.dumps(data), encoding="utf-8")

    def _queued(self, task_id: str, number: int, **pr) -> None:
        self._audit(task_id, number, A, "pid-a")
        (self.sb / ".guia" / "queue").mkdir(exist_ok=True)
        (self.sb / ".guia" / "queue" / f"{task_id}.msg").write_text(f"✨ feat({task_id}): t\n\ncorpo\n", encoding="utf-8")
        self.prs.append({"number": number, "head": A, "state": "OPEN", "mergeState": "CLEAN",
                         "checks": "pass", "patchIds": {A: "pid-a"}, **pr})
        self._save_prs()
        self._ok("queue", "add", task_id)
        self._ok("approve", task_id)

    def _save_prs(self) -> None:
        Path(str(self.fixture) + ".prs.json").write_text(json.dumps(self.prs), encoding="utf-8")

    def _items(self) -> dict[str, dict]:
        data = json.loads((self.sb / ".guia" / "queue.json").read_text(encoding="utf-8"))
        return {item["id"]: item for item in data["items"]}

    def _status(self, task_id: str) -> str:
        tasks = json.loads((self.sb / ".guia" / "tasks.json").read_text(encoding="utf-8"))["tasks"]
        return next(t for t in tasks if t["id"] == task_id)["status"]

    def test_conflict_stays_in_the_queue_and_the_next_one_integrates(self) -> None:
        self._queued("D-001", 1, mergeState="DIRTY")
        self._queued("D-002", 2)
        out = self._ok("queue", "run").stdout
        self.assertIn("D-001: CONFLITO", out)
        item = self._items()["D-001"]
        self.assertEqual(item["state"], "conflict")
        self.assertIn("conflito com a base", item["conflictReason"])
        self.assertEqual(self._status("D-001"), "Na fila", "nao volta ao autor")
        self.assertEqual(self._status("D-002"), "Integrada", "a fila segue")
        self.assertIn("o gerente da fila resolve", self._ok("queue").stdout)

    def test_changed_content_is_a_conflict_for_the_manager(self) -> None:
        self._queued("D-001", 1, mergeState="BEHIND", afterUpdate={"head": B}, patchIds={A: "pid-a", B: "pid-outro"})
        self._ok("queue", "run")
        self.assertEqual(self._items()["D-001"]["state"], "conflict")
        self.assertIn("mudou depois da auditoria", self._items()["D-001"]["conflictReason"])

    def test_resolved_conflict_goes_back_to_waiting_and_integrates(self) -> None:
        self._queued("D-001", 1, mergeState="DIRTY")
        self._ok("queue", "run")
        # o gerente resolveu: head novo B, auditado (delta), PR limpo
        self._audit("D-001", 1, B, "pid-b")
        self.prs[0].update(head=B, mergeState="CLEAN", patchIds={B: "pid-b"})
        self._save_prs()
        self._ok("queue", "add", "D-001")
        item = self._items()["D-001"]
        self.assertEqual((item["state"], item["auditedSha"], item["conflictReason"]), ("waiting", B, None))
        self.assertEqual(item["approval"]["by"], "user", "nada sensivel novo: a aprovacao do dono fica")
        self.assertEqual(len(self._items()), 1, "sem duplicar")
        self._ok("queue", "run")
        self.assertEqual(self._status("D-001"), "Integrada")

    def test_default_still_returns_to_the_author(self) -> None:
        (self.sb / ".guia" / "process.json").write_text(json.dumps({"delivery": {"mode": "pr"}}), encoding="utf-8")
        self._queued("D-001", 1, mergeState="DIRTY")
        self._ok("queue", "run")
        self.assertEqual(self._status("D-001"), "Em desenvolvimento")
        self.assertNotIn("D-001", self._items())


if __name__ == "__main__":
    unittest.main()
