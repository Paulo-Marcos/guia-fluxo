"""D-157: voltar ao chat - a demanda guarda o nome do chat, e quem a devolve aponta para ele.

`guia chat` sugere um nome estavel (sem a etiqueta de status) e grava o nome
do chat em que a demanda e feita. Quando a fila devolve ou deixa pendente, a
mensagem diz "volte ao chat: ..."; `next` e `status --all` tambem mostram.
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

CHAT = "D-001 ✨ Mostrar a nota"


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class ChatReturnTests(unittest.TestCase):
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
        (self.sb / ".guia" / "process.json").write_text(json.dumps(
            {"delivery": {"mode": "pr"}, "autonomy": {"default": "pilot", "ceiling": "pilot"}}), encoding="utf-8")
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

    def _set(self, **fields) -> None:
        path = self.sb / ".guia" / "tasks.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["tasks"][0].update(fields)
        path.write_text(json.dumps(data), encoding="utf-8")

    def test_suggests_a_stable_name_and_records_the_chat(self) -> None:
        out = self._ok("chat", "D-001").stdout
        self.assertIn(f"NOME DO CHAT: {CHAT}", out)
        self.assertNotIn("#DEV", out, "sem a etiqueta de status, que muda")
        self._ok("chat", "D-001", "--title", "Chat das notas")
        data = json.loads(self._ok("chat", "D-001", "--json").stdout)
        self.assertEqual((data["chat"], data["suggested"]), ("Chat das notas", CHAT))

    def test_returned_demand_points_to_its_chat(self) -> None:
        self._ok("chat", "D-001", "--title", CHAT)
        self._set(queue={"returnReason": "conflito com a base"})
        step = json.loads(self._ok("next", "D-001", "--json").stdout)
        self.assertEqual(step["chat"], CHAT)
        self.assertIn(f"[chat: {CHAT}]", self._ok("next", "D-001").stdout)
        board = self._ok("status", "--all").stdout
        self.assertIn("Pendencias:", board)
        self.assertIn(f"devolvida: conflito com a base - volte ao chat: {CHAT}", board)

    def test_integrated_pending_lists_why_and_the_chat(self) -> None:
        self._ok("chat", "D-001", "--title", CHAT)
        self._set(status="Integrada", autoFinish={"checks": [{"check": "tipo permitido", "ok": False, "evidence": "x"}]})
        board = self._ok("status", "--all").stdout
        self.assertIn(f"integrada; fechar e do dono (tipo permitido) - volte ao chat: {CHAT}", board)

    def test_plugin_tells_the_agent_to_name_and_record_the_chat(self) -> None:
        body = (REPO_ROOT / "plugins" / "guia" / "commands" / "feature.md").read_text(encoding="utf-8")
        for piece in ("chat <D-NNN>", "--title", "Always show the chat name"):
            self.assertIn(piece, body)


if __name__ == "__main__":
    unittest.main()
