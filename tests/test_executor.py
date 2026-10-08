"""D-127: o executor da fila (R5 + R8) contra PRs falsos com estados roteirizados.

`guia queue run` integra um PR por vez: le o PR, confere o head contra a
auditoria (patch-id igual carrega o marcador; diferente devolve), atualiza a
branch atrasada, espera os checks, mergeia com `--match-head-commit` e a
mensagem da fila. Devolver tira o item da fila, volta a demanda a
`Em desenvolvimento` com o motivo, e o executor segue. Uma lease garante um
executor por repositorio.

O fixture (`<GUIA_GH_FIXTURE>.prs.json`) roteiriza cada PR: head, estado de
merge, checks, patch-ids por SHA e o que o `update-branch` faz.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from conftest_paths import CORE_LOCK, CORE_SRC

A, B, C = "a" * 40, "b" * 40, "c" * 40


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class ExecutorTests(unittest.TestCase):
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
        self.fixture = self.sb / "gh.json"
        self.fixture.write_text(json.dumps({"__auth__": True}), encoding="utf-8")
        self.prs: list[dict] = []
        for title in ("primeira", "segunda"):
            self._ok("feature", title)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "core/src/guia.py", *args],
            cwd=self.sb, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "GUIA_GH_FIXTURE": str(self.fixture)},
        )

    def _ok(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = self._run(*args)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def _queued(self, task_id: str, number: int, **pr) -> None:
        """Demanda auditada no head A, na fila e aprovada; PR roteirizado."""
        path = self.sb / ".guia" / "tasks.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for task in data["tasks"]:
            if task["id"] == task_id:
                task["status"] = "Em PR"
                task["pr"] = {"number": number, "url": "u", "branch": f"b{number}", "head": A}
                task["audit"] = {"result": "approved", "auditedSha": A, "auditedPatchId": "pid-a"}
        path.write_text(json.dumps(data), encoding="utf-8")
        (self.sb / ".guia" / "queue").mkdir(exist_ok=True)
        (self.sb / ".guia" / "queue" / f"{task_id}.msg").write_text(
            f"✨ feat({task_id}): titulo\n\ncorpo do porque\n", encoding="utf-8"
        )
        self.prs.append({"number": number, "head": A, "state": "OPEN", "mergeState": "CLEAN",
                         "checks": "pass", "patchIds": {A: "pid-a"}, **pr})
        Path(str(self.fixture) + ".prs.json").write_text(json.dumps(self.prs), encoding="utf-8")
        self._ok("queue", "add", task_id)
        self._ok("approve", task_id)

    def _pr(self, number: int) -> dict:
        prs = json.loads(Path(str(self.fixture) + ".prs.json").read_text(encoding="utf-8"))
        return next(pr for pr in prs if pr["number"] == number)

    def _task(self, task_id: str) -> dict:
        tasks = json.loads((self.sb / ".guia" / "tasks.json").read_text(encoding="utf-8"))["tasks"]
        return next(t for t in tasks if t["id"] == task_id)

    def _queue_ids(self) -> list[str]:
        return [i["id"] for i in json.loads((self.sb / ".guia" / "queue.json").read_text(encoding="utf-8"))["items"]]

    def _comments(self) -> list[dict]:
        path = Path(str(self.fixture) + ".comments.json")
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []

    def test_clean_pr_is_merged_with_the_queued_message(self) -> None:
        self._queued("D-001", 1)
        self._ok("queue", "run")
        merged = self._pr(1)["merged"]
        self.assertEqual(merged["matchHead"], A)
        self.assertEqual(merged["subject"], "✨ feat(D-001): titulo (#1)")
        self.assertIn("corpo do porque", merged["body"])
        self.assertEqual(self._queue_ids(), [])
        self.assertEqual(self._task("D-001")["status"], "Integrada")

    def test_clean_rebase_carries_the_audit(self) -> None:
        self._queued("D-001", 1, mergeState="BEHIND", afterUpdate={"head": B}, patchIds={A: "pid-a", B: "pid-a"})
        self._ok("queue", "run")
        marker = self._comments()[0]["body"]
        self.assertIn(f"<!-- auditoria-aprovada sha={B} -->", marker)
        self.assertIn(f"carry-from={A}", marker)
        self.assertEqual(self._pr(1)["merged"]["matchHead"], B)

    def test_changed_patch_returns_and_the_next_item_still_integrates(self) -> None:
        self._queued("D-001", 1, mergeState="BEHIND", afterUpdate={"head": B}, patchIds={A: "pid-a", B: "pid-outro"})
        self._queued("D-002", 2)
        self._ok("queue", "run")
        self.assertNotIn("merged", self._pr(1))
        returned = self._task("D-001")
        self.assertEqual(returned["status"], "Em desenvolvimento")
        self.assertIn("mudou depois da auditoria", returned["queue"]["returnReason"])
        self.assertEqual(self._task("D-002")["status"], "Integrada")
        self.assertEqual(self._queue_ids(), [])

    def test_red_check_and_conflict_return(self) -> None:
        self._queued("D-001", 1, checks="fail", failing=["pytest (ubuntu)"])
        self._queued("D-002", 2, mergeState="BEHIND", afterUpdate={"conflict": True})
        self._ok("queue", "run")
        self.assertIn("pytest (ubuntu)", self._task("D-001")["queue"]["returnReason"])
        self.assertIn("conflito", self._task("D-002")["queue"]["returnReason"])

    def test_once_integrates_a_single_item(self) -> None:
        self._queued("D-001", 1)
        self._queued("D-002", 2)
        self._ok("queue", "run", "--once")
        self.assertEqual(self._queue_ids(), ["D-002"])

    def test_paused_queue_does_nothing(self) -> None:
        self._queued("D-001", 1)
        self._ok("queue", "pause", "--reason", "manutencao")
        self._ok("queue", "run")
        self.assertNotIn("merged", self._pr(1))

    def test_live_lease_refuses_and_stale_lease_is_taken(self) -> None:
        self._queued("D-001", 1)
        lease = self.sb / ".guia" / "queue" / "executor.lease"
        lease.write_text(json.dumps({"pid": 1, "host": "outro", "heartbeat": time.time()}), encoding="utf-8")
        result = self._run("queue", "run")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outro", result.stdout + result.stderr)
        lease.write_text(json.dumps({"pid": 1, "host": "outro", "heartbeat": time.time() - 3600}), encoding="utf-8")
        self._ok("queue", "run")
        self.assertEqual(self._task("D-001")["status"], "Integrada")
        self.assertFalse(lease.exists(), "lease liberada no fim")

    def test_blocked_by_protection_waits_instead_of_returning(self) -> None:
        """Checks verdes, mas a protecao ainda nao liberou (ex.: o status da
        auditoria sendo gravado): nao e culpa do autor - o item espera."""
        process = json.loads((self.sb / ".guia" / "process.json").read_text(encoding="utf-8"))
        process["delivery"]["queue"] = {"ciTimeoutMinutes": 0.01}
        (self.sb / ".guia" / "process.json").write_text(json.dumps(process), encoding="utf-8")
        self._queued("D-001", 1, mergeState="BLOCKED")
        self._ok("queue", "run")
        self.assertNotIn("merged", self._pr(1))
        self.assertEqual(self._queue_ids(), ["D-001"], "continua na fila")
        self.assertEqual(self._task("D-001")["status"], "Na fila", "nao foi devolvida")


if __name__ == "__main__":
    unittest.main()
