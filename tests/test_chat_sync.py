"""D-194: reconciliar o nome dos chats com a etapa da demanda.

O rename da D-188 dependia de um chat gerente ler a linha do `queue run`;
com o executor no terminal ninguem a lia e o chat ficava com o nome velho.
Agora cada demanda guarda o ultimo nome aplicado a sua sessao
(`chat.applied`) e qualquer chat do Guia varre as pendentes (`chat --pending`,
e as mesmas linhas em `next`/`status`), aplica e confirma (`chat --applied`).
Recusa (`chat --refused`) vira aviso e nao volta ate a etapa mudar. E o
literal "self" nunca e gravado como sessao (a D-191 gravou).
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

SESSION = "local_0000aaaa-1111-2222-3333-444455556666"
PREFIX = "RENOMEIE O CHAT: "


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class ChatSyncTests(unittest.TestCase):
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
        self._ok("feature", "Mostrar a nota")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, "core/src/guia.py", *args], cwd=self.sb, capture_output=True,
                              text=True, encoding="utf-8", env={**os.environ, "PYTHONUTF8": "1"})

    def _ok(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = self._run(*args)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def _task(self) -> dict:
        return json.loads((self.sb / ".guia" / "tasks.json").read_text(encoding="utf-8"))["tasks"][0]

    def _set_chat(self, chat: dict) -> None:
        path = self.sb / ".guia" / "tasks.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["tasks"][0]["chat"] = chat
        path.write_text(json.dumps(data), encoding="utf-8")

    def _pending(self) -> list[dict]:
        return json.loads(self._ok("chat", "--pending", "--json").stdout)["pending"]

    def _title(self) -> str:
        return self._ok("status", "D-001").stdout.split("NOME DA DEMANDA: ")[1].splitlines()[0]

    def test_self_is_refused_as_session(self) -> None:
        result = self._run("chat", "D-001", "--title", "x", "--session", "self")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("get_session", result.stdout + result.stderr)
        self.assertNotIn("session", self._task().get("chat") or {})

    def test_legacy_self_session_is_not_listed(self) -> None:
        self._set_chat({"title": "x", "session": "self"})
        self.assertEqual(self._pending(), [])

    def test_pending_until_applied_and_again_when_the_stage_changes(self) -> None:
        self._ok("chat", "D-001", "--title", "x", "--session", SESSION)
        title = self._title()
        self.assertEqual(self._pending(), [{"task": "D-001", "session": SESSION, "title": title}])
        self.assertIn(f"{PREFIX}{SESSION} -> {title}", self._ok("chat", "--pending").stdout)

        self._ok("chat", "D-001", "--applied", title)
        self.assertEqual(self._task()["chat"]["applied"], title)
        self.assertEqual(self._pending(), [])
        self.assertNotIn(PREFIX, self._ok("next", "D-001").stdout)

        self._ok("ready", "D-001", "--summary", "s")
        new_title = self._title()
        self.assertNotEqual(new_title, title)
        self.assertEqual([p["title"] for p in self._pending()], [new_title])

    def test_refusal_warns_once_and_is_not_repeated(self) -> None:
        self._ok("chat", "D-001", "--title", "x", "--session", SESSION)
        title = self._title()
        out = self._ok("chat", "D-001", "--refused", title, "--reason", "titulo do dono").stdout
        self.assertIn("aviso", out.lower())
        self.assertEqual(self._pending(), [])
        self.assertNotIn(PREFIX, self._ok("status", "D-001").stdout)
        self._ok("ready", "D-001", "--summary", "s")
        self.assertEqual(len(self._pending()), 1)

    def test_next_and_status_list_the_pending_renames(self) -> None:
        self._ok("chat", "D-001", "--title", "x", "--session", SESSION)
        line = f"{PREFIX}{SESSION} -> {self._title()}"
        self.assertIn(line, self._ok("next", "D-001").stdout)
        self.assertIn(line, self._ok("status", "D-001").stdout)
        self.assertIn(line, self._ok("status", "--all").stdout)
        step = json.loads(self._ok("next", "D-001", "--json").stdout)
        self.assertEqual(step["chatRenames"][0]["session"], SESSION)


class ChatSyncInstructionsTests(unittest.TestCase):
    def test_commands_tell_every_chat_to_sweep(self) -> None:
        for verb in ("start", "status", "ready", "queue"):
            body = (REPO_ROOT / "plugins" / "guia" / "commands" / f"{verb}.md").read_text(encoding="utf-8")
            for piece in ("D-194", "--applied", "--refused", "set_session_title"):
                self.assertIn(piece, body, msg=verb)


if __name__ == "__main__":
    unittest.main()
