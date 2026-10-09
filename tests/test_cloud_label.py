"""D-130: PRs da nuvem entram na fila pelo rotulo `guia:fila` (R5 Nuvem).

A sessao na nuvem nao alcanca o `.guia/` do PC: abre o PR e poe o rotulo. O
executor (ou `guia queue import`) traz o PR para a fila SEM auditoria - a
demanda e achada pela branch `d-NNN-*`. Sem auditoria nada integra. No PC,
`guia worktree add` segue a branch que a nuvem empurrou, e `queue add` completa
o item importado depois da auditoria.
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


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=", *args],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8",
    )


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class CloudLabelTests(unittest.TestCase):
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
        # a "nuvem": clona, commita numa branch de demanda e empurra
        cloud = base / "nuvem"
        for args in (("clone", "-q", str(remote), str(cloud)),):
            self.assertEqual(_git(base, *args).returncode, 0)
        for args in (("checkout", "-q", "-b", "d-001-feito-na-nuvem", "origin/main"),):
            self.assertEqual(_git(cloud, *args).returncode, 0)
        (cloud / "app.txt").write_text("app da nuvem\n", encoding="utf-8")
        for args in (("commit", "-q", "-am", "nuvem"), ("push", "-q", "origin", "d-001-feito-na-nuvem")):
            self.assertEqual(_git(cloud, *args).returncode, 0, msg=str(args))
        self.cloud_head = _git(cloud, "rev-parse", "HEAD").stdout.strip()
        self.fixture = base / "gh.json"
        self.fixture.write_text(json.dumps({"__auth__": True, "__labeled__": [
            {"number": 7, "title": "feito na nuvem", "headRefName": "d-001-feito-na-nuvem", "headRefOid": self.cloud_head},
            {"number": 8, "title": "sem demanda", "headRefName": "feature-solta", "headRefOid": "f" * 40},
        ]}), encoding="utf-8")
        Path(str(self.fixture) + ".prs.json").write_text(json.dumps([
            {"number": 7, "head": self.cloud_head, "state": "OPEN", "mergeState": "CLEAN", "checks": "pass",
             "patchIds": {self.cloud_head: "p"}},
        ]), encoding="utf-8")
        self._ok("feature", "Feito na nuvem")
        self.base = base

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.main / "core" / "src" / "guia.py"), *args],
            cwd=cwd, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "GUIA_GH_FIXTURE": str(self.fixture)},
        )

    def _ok(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        result = self._run(cwd or self.main, *args)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def _queue(self) -> dict:
        return json.loads((self.main / ".guia" / "queue.json").read_text(encoding="utf-8"))

    def _task(self) -> dict:
        return json.loads((self.main / ".guia" / "tasks.json").read_text(encoding="utf-8"))["tasks"][0]

    def test_import_brings_the_labeled_pr_without_audit(self) -> None:
        out = self._ok("queue", "import").stdout
        items = self._queue()["items"]
        self.assertEqual([(i["id"], i["pr"], i["enqueuedBy"]) for i in items], [("D-001", 7, "cloud-label")])
        self.assertIsNone(items[0]["auditedSha"])
        self.assertIn("feature-solta", out, "PR sem demanda so gera aviso")
        self.assertEqual(self._task()["status"], "Na fila")
        listing = json.loads(self._ok("queue", "--json").stdout)
        self.assertIn("auditoria", listing["items"][0]["waiting"])
        self._ok("queue", "import")
        self.assertEqual(len(self._queue()["items"]), 1, "importar de novo nao duplica")

    def test_executor_imports_but_never_integrates_without_audit(self) -> None:
        self._ok("approve", "--all")
        self._ok("queue", "run")
        self.assertEqual([i["id"] for i in self._queue()["items"]], ["D-001"])
        prs = json.loads(Path(str(self.fixture) + ".prs.json").read_text(encoding="utf-8"))
        self.assertNotIn("merged", prs[0])

    def test_pc_worktree_follows_the_cloud_branch_and_add_completes_the_item(self) -> None:
        self._ok("queue", "import")
        self._ok("worktree", "add", "D-001")
        worktree = self.base / "app-d001"
        self.assertEqual(_git(worktree, "rev-parse", "HEAD").stdout.strip(), self.cloud_head)
        self.assertEqual((worktree / "app.txt").read_text(encoding="utf-8"), "app da nuvem\n")
        # auditoria e mensagem de squash como o ship/audit gravariam (sintetico)
        path = self.main / ".guia" / "tasks.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        task = data["tasks"][0]
        task["audit"] = {"result": "approved", "auditedSha": self.cloud_head, "auditedPatchId": "p"}
        path.write_text(json.dumps(data), encoding="utf-8")
        (self.main / ".guia" / "queue").mkdir(exist_ok=True)
        (self.main / ".guia" / "queue" / "D-001.msg").write_text("x(D-001): nuvem\n\ncorpo\n", encoding="utf-8")
        self._ok("queue", "add", "D-001")
        item = self._queue()["items"][0]
        self.assertEqual(item["auditedSha"], self.cloud_head)
        self._ok("approve", "D-001")
        self._ok("queue", "run")
        self.assertEqual(self._queue()["items"], [])
        self.assertEqual(self._task()["status"], "Integrada")


if __name__ == "__main__":
    unittest.main()
