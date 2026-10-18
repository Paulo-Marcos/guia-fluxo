"""D-188: a fila renomeia o chat da demanda ao integrar.

O chat grava o proprio `sessionId` (`chat --session`). Ao integrar, o
`queue run` imprime `RENOMEIE O CHAT: <sessionId> -> <NOME DA DEMANDA>`; o
executor nao fala com o app, quem renomeia e o chat gerente da fila. O
GitHub e roteirizado pelo fixture; o git e real.
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

from conftest_paths import CORE_LOCK, CORE_SRC, REPO_ROOT

A = "a" * 40
PREFIX = "RENOMEIE O CHAT: "


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=", *args],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8",
    )


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class ChatRenameByQueueTests(unittest.TestCase):
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
        self._ok("feature", "Mostrar a nota")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "core/src/guia.py", *args],
            cwd=self.main, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "GUIA_GH_FIXTURE": str(self.fixture), "PYTHONUTF8": "1"},
        )

    def _ok(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = self._run(*args)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def _queued(self) -> None:
        path = self.main / ".guia" / "tasks.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        task = data["tasks"][0]
        task["status"] = "Em PR"
        task["pr"] = {"number": 1, "url": "u", "branch": "b1", "head": A}
        task["audit"] = {"result": "approved", "auditedSha": A, "auditedPatchId": "p"}
        path.write_text(json.dumps(data), encoding="utf-8")
        (self.main / ".guia" / "queue").mkdir(exist_ok=True)
        (self.main / ".guia" / "queue" / "D-001.msg").write_text("x(D-001): t\n\ncorpo\n", encoding="utf-8")
        prs = [{"number": 1, "head": A, "state": "OPEN", "mergeState": "CLEAN",
                "checks": "pass", "patchIds": {A: "p"}, "mainCi": "pass"}]
        Path(str(self.fixture) + ".prs.json").write_text(json.dumps(prs), encoding="utf-8")
        self._ok("queue", "add", "D-001")
        self._ok("approve", "D-001")

    def _rename_lines(self) -> list[str]:
        return [line for line in self._ok("queue", "run").stdout.splitlines() if line.startswith(PREFIX)]

    def test_records_the_session_without_losing_the_title(self) -> None:
        self._ok("chat", "D-001", "--title", "Chat das notas")
        out = self._ok("chat", "D-001", "--session", "local_123").stdout
        self.assertIn("NOME DO CHAT: Chat das notas", out)
        self.assertIn("SESSAO DO CHAT: local_123", out)
        self._ok("chat", "D-001", "--title", "Outro nome")
        data = json.loads(self._ok("chat", "D-001", "--json").stdout)
        self.assertEqual((data["chat"], data["session"]), ("Outro nome", "local_123"))
        self.assertIn('"session": "local_123"', self._ok("status", "D-001").stdout)

    def test_integrated_demand_with_a_session_asks_to_rename_its_chat(self) -> None:
        self._ok("chat", "D-001", "--title", "Chat das notas", "--session", "local_abc")
        self._queued()
        lines = self._rename_lines()
        self.assertEqual(len(lines), 1, msg=lines)
        session, title = lines[0].removeprefix(PREFIX).split(" -> ")
        self.assertEqual(session, "local_abc")
        self.assertTrue(title.startswith("D-001 "), title)
        self.assertIn("#INTEGRADA", title)

    def test_integrated_demand_without_a_session_prints_no_rename(self) -> None:
        self._ok("chat", "D-001", "--title", "Chat das notas")
        self._queued()
        self.assertEqual(self._rename_lines(), [])

    def test_queue_manager_is_told_to_rename_the_chats(self) -> None:
        body = (REPO_ROOT / "plugins" / "guia" / "commands" / "queue-control.md").read_text(encoding="utf-8")
        for piece in ("RENOMEIE O CHAT: <sessionId> -> <NOME DA DEMANDA>", "set_session_title", "do not retry"):
            self.assertIn(piece, body)
        feature = (REPO_ROOT / "plugins" / "guia" / "commands" / "feature.md").read_text(encoding="utf-8")
        self.assertIn("--session <sessionId>", feature)


if __name__ == "__main__":
    unittest.main()
