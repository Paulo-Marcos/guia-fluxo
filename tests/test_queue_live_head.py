"""D-162: `queue add` confere a auditoria contra o head ATUAL do PR.

Regressao: depois de um rebase + push feito fora do `ship` (branch BEHIND), a
auditoria aprovava o head novo, mas o `queue add` comparava com o
`task.pr.head` gravado no `ship` e recusava - o contorno era um `ship` de novo,
com mais um portao completo. Agora o head vem do GitHub (`gh_pr_state`) e o
registro e atualizado; sem `gh`, vale o gravado, como antes.
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

OLD_HEAD = "a" * 40
NEW_HEAD = "b" * 40


class QueueAddLiveHeadTests(unittest.TestCase):
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
        self._ok("feature", "primeira")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, *args: str, fixture: bool = True) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        if fixture:
            env["GUIA_GH_FIXTURE"] = str(self.fixture)
        else:
            env.pop("GUIA_GH_FIXTURE", None)
        return subprocess.run(
            [sys.executable, "core/src/guia.py", *args],
            cwd=self.sb, capture_output=True, text=True, encoding="utf-8", env=env,
        )

    def _ok(self, *args: str, fixture: bool = True) -> subprocess.CompletedProcess[str]:
        result = self._run(*args, fixture=fixture)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def _shipped(self, recorded_head: str, audited: str, remote_head: str) -> None:
        """Ship gravou `recorded_head`; o GitHub esta em `remote_head`."""
        path = self.sb / ".guia" / "tasks.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        task = next(t for t in data["tasks"] if t["id"] == "D-001")
        task["status"] = "Em PR"
        task["pr"] = {"number": 1, "url": "u", "branch": "b-D-001", "head": recorded_head}
        task["audit"] = {"result": "approved", "auditedSha": audited, "auditedPatchId": "p"}
        path.write_text(json.dumps(data), encoding="utf-8")
        (self.sb / ".guia" / "queue").mkdir(exist_ok=True)
        (self.sb / ".guia" / "queue" / "D-001.msg").write_text("msg\n", encoding="utf-8")
        prs = [{"number": 1, "headRef": "b-D-001", "head": remote_head, "state": "OPEN"}]
        Path(str(self.fixture) + ".prs.json").write_text(json.dumps(prs), encoding="utf-8")

    def _recorded_head(self) -> str:
        tasks = json.loads((self.sb / ".guia" / "tasks.json").read_text(encoding="utf-8"))["tasks"]
        return next(t for t in tasks if t["id"] == "D-001")["pr"]["head"]

    def test_add_accepts_audit_of_the_live_head_after_rebase(self) -> None:
        self._shipped(recorded_head=OLD_HEAD, audited=NEW_HEAD, remote_head=NEW_HEAD)
        self._ok("queue", "add", "D-001")
        queue = json.loads((self.sb / ".guia" / "queue.json").read_text(encoding="utf-8"))
        self.assertEqual(queue["items"][0]["auditedSha"], NEW_HEAD)
        self.assertEqual(self._recorded_head(), NEW_HEAD, "o registro do PR deve seguir o head atual")

    def test_add_refuses_when_live_head_moved_past_the_audit(self) -> None:
        self._shipped(recorded_head=OLD_HEAD, audited=OLD_HEAD, remote_head=NEW_HEAD)
        result = self._run("queue", "add", "D-001")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(NEW_HEAD, result.stdout + result.stderr)

    def test_without_github_falls_back_to_recorded_head(self) -> None:
        self._shipped(recorded_head=OLD_HEAD, audited=OLD_HEAD, remote_head=NEW_HEAD)
        self._ok("queue", "add", "D-001", fixture=False)


if __name__ == "__main__":
    unittest.main()
