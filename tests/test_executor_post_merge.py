"""D-128: o que o executor faz depois do merge (R5, passo 6).

Remove o worktree da demanda (protocolo seguro da D-113), atualiza a arvore
principal (limpa: pull --ff-only; suja: so fetch, com aviso) e acompanha o
CI no commit do squash na main - vermelho congela a fila. `queue resume`
descongela. O GitHub e roteirizado pelo fixture; o git e real.
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

A = "a" * 40


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=", *args],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8",
    )


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class PostMergeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.main = base / "app"
        (self.main / "core" / "src").mkdir(parents=True)
        (self.main / "core" / "lock").mkdir(parents=True)
        for src in CORE_SRC.glob("*.py"):
            if not src.name.startswith("__"):
                shutil.copy2(src, self.main / "core" / "src" / src.name)
        shutil.copy2(CORE_LOCK / "lock_api.py", self.main / "core" / "lock" / "lock_api.py")
        (self.main / ".guia").mkdir()
        (self.main / ".guia" / "process.json").write_text(json.dumps({"delivery": {"mode": "pr"}}), encoding="utf-8")
        (self.main / ".gitignore").write_text(".guia/*\n!.guia/process.json\ncore/\n", encoding="utf-8")
        (self.main / "app.txt").write_text("app\n", encoding="utf-8")
        remote = base / "remote.git"
        _git(base, "init", "-q", "--bare", str(remote))
        for args in (("init", "-q", "-b", "main"), ("add", "."), ("commit", "-q", "-m", "init"),
                     ("remote", "add", "origin", str(remote)), ("push", "-q", "-u", "origin", "main")):
            self.assertEqual(_git(self.main, *args).returncode, 0, msg=str(args))
        self.fixture = base / "gh.json"
        self.fixture.write_text(json.dumps({"__auth__": True}), encoding="utf-8")
        self.prs: list[dict] = []
        for title in ("primeira", "segunda"):
            self._ok("feature", title)
        self._ok("worktree", "add", "D-001")
        self.worktree = base / "app-d001"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "core/src/guia.py", *args],
            cwd=self.main, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "GUIA_GH_FIXTURE": str(self.fixture)},
        )

    def _ok(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = self._run(*args)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def _queued(self, task_id: str, number: int, main_ci: str = "pass") -> None:
        path = self.main / ".guia" / "tasks.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for task in data["tasks"]:
            if task["id"] == task_id:
                task["status"] = "Em PR"
                task["pr"] = {"number": number, "url": "u", "branch": f"b{number}", "head": A}
                task["audit"] = {"result": "approved", "auditedSha": A, "auditedPatchId": "p"}
        path.write_text(json.dumps(data), encoding="utf-8")
        (self.main / ".guia" / "queue").mkdir(exist_ok=True)
        (self.main / ".guia" / "queue" / f"{task_id}.msg").write_text(f"x({task_id}): t\n\ncorpo\n", encoding="utf-8")
        self.prs.append({"number": number, "head": A, "state": "OPEN", "mergeState": "CLEAN",
                         "checks": "pass", "patchIds": {A: "p"}, "mainCi": main_ci})
        Path(str(self.fixture) + ".prs.json").write_text(json.dumps(self.prs), encoding="utf-8")
        self._ok("queue", "add", task_id)
        self._ok("approve", task_id)

    def _queue(self) -> dict:
        return json.loads((self.main / ".guia" / "queue.json").read_text(encoding="utf-8"))

    def test_worktree_is_removed_and_the_main_tree_is_pulled(self) -> None:
        self.assertTrue(self.worktree.exists())
        self._queued("D-001", 1)
        out = self._ok("queue", "run").stdout
        self.assertFalse(self.worktree.exists(), "worktree da demanda removido")
        self.assertIn("pull", out)
        task = json.loads((self.main / ".guia" / "tasks.json").read_text(encoding="utf-8"))["tasks"]
        self.assertEqual(next(t for t in task if t["id"] == "D-001")["status"], "Integrada")

    def test_dirty_main_tree_is_not_pulled(self) -> None:
        (self.main / "app.txt").write_text("trabalho do dono\n", encoding="utf-8")
        self._queued("D-001", 1)
        out = self._ok("queue", "run").stdout
        self.assertIn("suja", out)
        self.assertEqual((self.main / "app.txt").read_text(encoding="utf-8"), "trabalho do dono\n")

    def test_red_main_freezes_the_queue_until_resume(self) -> None:
        self._queued("D-001", 1, main_ci="fail")
        self._queued("D-002", 2)
        self._ok("queue", "run")
        queue = self._queue()
        self.assertIn("vermelha", queue["frozenReason"])
        self.assertEqual([i["id"] for i in queue["items"]], ["D-002"], "nada integra em cima da main quebrada")
        self.assertIn("CONGELADA", self._ok("queue").stdout)
        self._ok("queue", "resume")
        self.assertIsNone(self._queue()["frozenReason"])
        self._ok("queue", "run")
        self.assertEqual(self._queue()["items"], [])

    def test_pending_main_ci_does_not_freeze(self) -> None:
        self._queued("D-001", 1, main_ci="pending")
        out = self._ok("queue", "run").stdout
        self.assertIsNone(self._queue()["frozenReason"])
        self.assertIn("CI da main", out)


if __name__ == "__main__":
    unittest.main()
