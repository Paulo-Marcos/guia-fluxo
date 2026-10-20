"""D-190: todo chat que comeca uma demanda se renomeia e grava a sessao.

No gerador-cortes so 1 de 51 demandas gravou `chat.session`, entao o RENOMEIE
O CHAT da fila (D-188) quase nunca disparava: `epic` e `worktree` nao diziam
como renomear, e as filhas iniciadas em lote no chat do epico ficavam sem chat.
Agora todo command que inicia trabalho traz a receita inteira (ToolSearch +
set_session_title + `chat --title --session`), `next`/`status` avisam a demanda
em desenvolvimento sem sessao, o `.guia/chat-title.txt` orfao some e o motor
avisa quando o plugin instalado esta atras do que o marketplace ja tem.
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

COMMANDS = REPO_ROOT / "plugins" / "guia" / "commands"
# Todo command que comeca (ou retoma) trabalho numa demanda neste chat.
START_VERBS = ("feature", "bug", "chore", "start", "unblock", "promote", "epic", "worktree", "deps",
               "guia-fluxo")
CHAT = "D-001 ✨ Mostrar a nota"
SESSION = "local_abc"


class StartCommandsNameTheChatTests(unittest.TestCase):
    def test_every_start_command_carries_the_whole_rename_recipe(self) -> None:
        for verb in START_VERBS:
            body = (COMMANDS / f"{verb}.md").read_text(encoding="utf-8")
            with self.subTest(verb=verb):
                self.assertIn("select:mcp__ccd_session_mgmt__set_session_title", body)
                self.assertIn("mcp__ccd_session_mgmt__get_session", body)
                self.assertIn('--title "<name>" --session <sessionId>', body)


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class ChatWarningTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.sb = Path(self._tmp.name) / "proj"
        (self.sb / "core" / "src").mkdir(parents=True)
        (self.sb / "core" / "lock").mkdir(parents=True)
        for src in CORE_SRC.glob("*.py"):
            if not src.name.startswith("__"):
                shutil.copy2(src, self.sb / "core" / "src" / src.name)
        shutil.copy2(CORE_LOCK / "lock_api.py", self.sb / "core" / "lock" / "lock_api.py")
        subprocess.run(["git", "init", "-q"], cwd=self.sb, check=True, capture_output=True)
        (self.sb / ".guia").mkdir()
        (self.sb / ".guia" / "process.json").write_text(json.dumps(
            {"delivery": {"mode": "pr"}, "autonomy": {"default": "pilot", "ceiling": "pilot"}}), encoding="utf-8")
        self.claude = Path(self._tmp.name) / "claude"
        (self.claude / "plugins").mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _ok(self, *args: str) -> str:
        env = {**os.environ, "PYTHONUTF8": "1", "CLAUDE_CONFIG_DIR": str(self.claude)}
        result = subprocess.run([sys.executable, "core/src/guia.py", *args], cwd=self.sb, capture_output=True,
                                text=True, encoding="utf-8", env=env)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result.stdout

    def test_in_development_without_session_is_warned_until_recorded(self) -> None:
        self._ok("feature", "Mostrar a nota")
        for out in (self._ok("next", "D-001"), self._ok("status", "D-001"), self._ok("status", "--all")):
            self.assertIn("AVISO CHAT: D-001 sem chat registrado", out)
            self.assertIn(f'chat D-001 --title "{CHAT}" --session <sessionId>', out)
        self.assertIn("sem chat registrado", json.loads(self._ok("next", "D-001", "--json"))["chatWarning"])

        self._ok("chat", "D-001", "--title", CHAT)
        self.assertIn("AVISO CHAT: D-001 sem a sessao do chat", self._ok("next", "D-001"))

        self._ok("chat", "D-001", "--session", SESSION)
        for out in (self._ok("next", "D-001"), self._ok("status", "D-001"), self._ok("status", "--all")):
            self.assertNotIn("AVISO CHAT", out)
        self.assertIsNone(json.loads(self._ok("next", "D-001", "--json"))["chatWarning"])

    def test_planned_demand_is_not_warned(self) -> None:
        self._ok("feature", "Mostrar a nota", "--status", "planned")
        self.assertNotIn("AVISO CHAT", self._ok("next", "D-001"))

    def test_orphan_chat_title_file_is_removed(self) -> None:
        orphan = self.sb / ".guia" / "chat-title.txt"
        orphan.write_text("D-000 - #DEV - velho\n", encoding="utf-8")
        self._ok("feature", "Mostrar a nota")
        self.assertFalse(orphan.exists(), "legado de antes do ADR-0018")
        self.assertTrue((self.sb / ".guia" / "demand-title.txt").exists())

    def _install(self, installed: str, available: str) -> None:
        market = Path(self._tmp.name) / "market"
        (market / ".claude-plugin").mkdir(parents=True)
        (market / "plugins" / "guia" / ".claude-plugin").mkdir(parents=True)
        (market / ".claude-plugin" / "marketplace.json").write_text(json.dumps(
            {"name": "guia-fluxo", "plugins": [{"name": "guia", "source": "./plugins/guia"}]}), encoding="utf-8")
        (market / "plugins" / "guia" / ".claude-plugin" / "plugin.json").write_text(
            json.dumps({"name": "guia", "version": available}), encoding="utf-8")
        plugins = self.claude / "plugins"
        (plugins / "known_marketplaces.json").write_text(json.dumps(
            {"guia-fluxo": {"source": {"source": "directory", "path": str(market)},
                            "installLocation": str(market)}}), encoding="utf-8")
        (plugins / "installed_plugins.json").write_text(json.dumps(
            {"version": 2, "plugins": {"guia@guia-fluxo": [{"scope": "user", "version": installed}]}}),
            encoding="utf-8")

    def test_stale_plugin_is_warned(self) -> None:
        self._ok("feature", "Mostrar a nota")
        self._install("0.9.0", "0.10.0")
        out = self._ok("status", "D-001")
        self.assertIn("PLUGIN DESATUALIZADO: guia@guia-fluxo 0.9.0 instalado, 0.10.0 disponivel", out)
        self.assertIn("/plugin update guia@guia-fluxo", out)

    def test_current_plugin_is_quiet(self) -> None:
        self._ok("feature", "Mostrar a nota")
        self._install("0.10.0", "0.10.0")
        self.assertNotIn("PLUGIN DESATUALIZADO", self._ok("status", "D-001"))


if __name__ == "__main__":
    unittest.main()
