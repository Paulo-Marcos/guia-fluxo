"""D-199 (ADR-0023): chat controlador e sessoes executoras.

Um chat controlador abria uma sessao por demanda, mas as follow-ups abertas
pelas executoras (D-195, D-196, D-197) ficaram sem `chat.session`: o
`chat --pending` da D-194 nao as via e o controlador renomeou os chats a mao.
Agora a demanda guarda o papel de quem a faz (`chat --role`) e o controlador
(`chat --controller`), `status` e o painel mostram os dois, `chat --pending`
acusa demanda aberta sem sessao, e a regra esta nos commands e no AGENTS.md.
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

from conftest_paths import CORE_LOCK, CORE_SRC, REPO_ROOT, ensure_core_importable

ensure_core_importable()

import _dashboard  # noqa: E402
from _task_view import role_line  # noqa: E402

EXECUTOR = "local_0000aaaa-1111-2222-3333-444455556666"
CONTROLLER = "local_9999ffff-8888-7777-6666-555544443333"
COMMANDS = REPO_ROOT / "plugins" / "guia" / "commands"
START_VERBS = ("feature", "bug", "chore", "start", "unblock", "promote", "epic", "worktree", "guia-fluxo")


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class ChatRoleCliTests(unittest.TestCase):
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

    def _ok(self, *args: str) -> str:
        result = self._run(*args)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result.stdout

    def _chat(self) -> dict:
        return json.loads((self.sb / ".guia" / "tasks.json").read_text(encoding="utf-8"))["tasks"][0]["chat"]

    def test_executor_records_role_and_controller_and_status_shows_them(self) -> None:
        out = self._ok("chat", "D-001", "--title", "D-001 ✨ Mostrar a nota", "--session", EXECUTOR,
                       "--controller", CONTROLLER)
        self.assertIn(f"PAPEL DO CHAT: executora (controlador {CONTROLLER})", out)
        chat = self._chat()
        self.assertEqual((chat["role"], chat["controller"], chat["session"]), ("executor", CONTROLLER, EXECUTOR))
        self.assertIn(f"Chat: D-001 ✨ Mostrar a nota · executora (controlador {CONTROLLER})",
                      self._ok("status", "D-001"))
        payload = json.loads(self._ok("chat", "D-001", "--json"))
        self.assertEqual((payload["role"], payload["controller"]), ("executor", CONTROLLER))

    def test_controller_role_has_no_controller(self) -> None:
        self._ok("chat", "D-001", "--title", "x", "--controller", CONTROLLER)
        self._ok("chat", "D-001", "--role", "controller")
        self.assertEqual(self._chat()["role"], "controller")
        self.assertNotIn("controller", self._chat())
        refused = self._run("chat", "D-001", "--role", "controller", "--controller", CONTROLLER)
        self.assertNotEqual(refused.returncode, 0)

    def test_self_is_refused_as_controller(self) -> None:
        result = self._run("chat", "D-001", "--title", "x", "--controller", "self")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("get_session", result.stdout + result.stderr)

    def test_pending_lists_open_demand_without_session_until_recorded(self) -> None:
        missing = json.loads(self._ok("chat", "--pending", "--json"))["missing"]
        self.assertEqual([m["task"] for m in missing], ["D-001"])
        self.assertIn("AVISO CHAT: D-001 (Em desenvolvimento) sem a sessao do chat", self._ok("chat", "--pending"))
        self._ok("chat", "D-001", "--title", "x", "--session", EXECUTOR, "--controller", CONTROLLER)
        self.assertEqual(json.loads(self._ok("chat", "--pending", "--json"))["missing"], [])

    def test_planned_follow_up_is_not_nagged_before_it_starts(self) -> None:
        self._ok("bug", "Follow-up", "--status", "planned")
        missing = json.loads(self._ok("chat", "--pending", "--json"))["missing"]
        self.assertNotIn("D-002", [m["task"] for m in missing])


class DashboardShowsRoleTests(unittest.TestCase):
    def test_card_and_detail_carry_role_and_controller(self) -> None:
        task = {"id": "D-001", "kind": "feature", "title": "x", "status": "Em desenvolvimento",
                "chat": {"title": "D-001 ✨ x", "session": EXECUTOR, "role": "executor", "controller": CONTROLLER}}
        card = _dashboard._card(task, {})
        self.assertEqual(card["chatRole"], f"executora (controlador {CONTROLLER})")
        self.assertEqual(card["detail"]["chat"]["controller"], CONTROLLER)
        self.assertIsNone(_dashboard._card({**task, "chat": {"title": "y"}}, {})["chatRole"])

    def test_role_line(self) -> None:
        self.assertEqual(role_line({"role": "controller"}), "controlador")
        self.assertIsNone(role_line(None))


class RuleIsWrittenTests(unittest.TestCase):
    def test_start_commands_carry_the_controller_executor_rule(self) -> None:
        for verb in START_VERBS:
            body = (COMMANDS / f"{verb}.md").read_text(encoding="utf-8")
            with self.subTest(verb=verb):
                self.assertIn("D-199, ADR-0023", body)
                self.assertIn("--role executor --controller", body)
                self.assertIn("in the developer's words", body)

    def test_agents_md_and_adr(self) -> None:
        agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("## Chat controlador e sessoes executoras", agents)
        self.assertIn("com as palavras do dono", agents)
        self.assertTrue((REPO_ROOT / "docs" / "adr" / "0023-chat-controlador-e-sessoes-executoras.md").exists())


if __name__ == "__main__":
    unittest.main()
