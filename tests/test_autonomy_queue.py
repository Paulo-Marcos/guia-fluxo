"""D-134: nivel queue aprova implicito, e alwaysHuman sempre para no humano (R6).

Com nivel >= queue, `queue add` entra aprovado (`approval.by = autonomy`) -
salvo quando o diff do PR toca um caminho de `autonomy.alwaysHuman` ou a
mensagem de squash traz `[unlock:<trava>]` de uma trava de
`autonomy.alwaysHumanLocks` ("*" = todas). Os caminhos vem do git (diff da
branch contra a base), nunca da lista que o agente declara.
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
class AutonomyQueueTests(unittest.TestCase):
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
        self.process = {"delivery": {"mode": "pr"}, "autonomy": {"default": "queue", "ceiling": "pilot"}}
        self._write_process()
        # .guia/ fora do git: o checkout da branch nao pode voltar o process.json.
        (self.main / ".gitignore").write_text(".guia/\ncore/\n", encoding="utf-8")
        (self.main / "app.txt").write_text("app\n", encoding="utf-8")
        self.remote = base / "remote.git"
        _git(base, "init", "-q", "--bare", str(self.remote))
        for args in (("init", "-q", "-b", "main"), ("add", "."), ("commit", "-q", "-m", "init"),
                     ("remote", "add", "origin", str(self.remote)), ("push", "-q", "-u", "origin", "main")):
            self.assertEqual(_git(self.main, *args).returncode, 0, msg=str(args))
        self._ok("chore", "mexer")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write_process(self) -> None:
        (self.main / ".guia" / "process.json").write_text(json.dumps(self.process), encoding="utf-8")

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "core/src/guia.py", *args],
            cwd=self.main, capture_output=True, text=True, encoding="utf-8",
        )

    def _ok(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = self._run(*args)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def _pr_branch(self, files: dict[str, str], message: str = "x(D-001): t\n\ncorpo\n") -> None:
        """Branch d-001 no remoto com `files`, e a demanda como ship + audit gravariam."""
        _git(self.main, "checkout", "-q", "-b", "d-001-mexer")
        for rel, content in files.items():
            path = self.main / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        _git(self.main, "add", "-A")
        _git(self.main, "commit", "-q", "-m", "mudanca")
        _git(self.main, "push", "-q", "origin", "d-001-mexer")
        head = _git(self.main, "rev-parse", "HEAD").stdout.strip()
        _git(self.main, "checkout", "-q", "main")
        path = self.main / ".guia" / "tasks.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        task = data["tasks"][0]
        task["status"] = "Em PR"
        task["pr"] = {"number": 1, "url": "u", "branch": "d-001-mexer", "head": head}
        task["audit"] = {"result": "approved", "auditedSha": head, "auditedPatchId": "p"}
        path.write_text(json.dumps(data), encoding="utf-8")
        (self.main / ".guia" / "queue").mkdir(exist_ok=True)
        (self.main / ".guia" / "queue" / "D-001.msg").write_text(message, encoding="utf-8")

    def _item(self) -> dict:
        return json.loads((self.main / ".guia" / "queue.json").read_text(encoding="utf-8"))["items"][0]

    def _waiting(self) -> str | None:
        return json.loads(self._ok("queue", "--json").stdout)["items"][0]["waiting"]

    def test_queue_level_enters_approved(self) -> None:
        self._pr_branch({"app.txt": "novo\n"})
        self._ok("queue", "add", "D-001")
        self.assertEqual(self._item()["approval"]["by"], "autonomy")
        self.assertIsNone(self._waiting())

    def test_pr_level_still_needs_the_user(self) -> None:
        self.process["autonomy"]["default"] = "pr"
        self._write_process()
        self._pr_branch({"app.txt": "novo\n"})
        self._ok("queue", "add", "D-001")
        self.assertIsNone(self._item()["approval"])

    def test_always_human_path_from_git_waits_for_the_user(self) -> None:
        self._pr_branch({"app.txt": "novo\n", ".github/workflows/ci.yml": "on: push\n"})
        out = self._ok("queue", "add", "D-001").stdout
        self.assertIsNone(self._item()["approval"])
        self.assertIn(".github/workflows/ci.yml", self._waiting())
        self.assertIn("alwaysHuman", out)

    def test_unlock_mark_waits_unless_the_lock_is_released(self) -> None:
        message = "x(D-001): t\n\n[unlock:adicoes] motivo: arquivo novo\n"
        self._pr_branch({"novo.txt": "n\n"}, message)
        self._ok("queue", "add", "D-001")
        self.assertIsNone(self._item()["approval"])
        self.assertIn("adicoes", self._waiting())
        # a trava fora de alwaysHumanLocks nao segura
        self._ok("queue", "remove", "D-001")
        self.process["autonomy"]["alwaysHumanLocks"] = ["homologado"]
        self._write_process()
        self._ok("queue", "add", "D-001")
        self.assertEqual(self._item()["approval"]["by"], "autonomy")


if __name__ == "__main__":
    unittest.main()
