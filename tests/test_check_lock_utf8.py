"""D-116: check-lock le e escreve o git log em UTF-8.

`audit`/`history` liam o `git log` com a codificacao do sistema (cp1252 no
Windows) e o byte 0x90 do emoji 🐛 (assunto gitmoji de correcao) estourava
UnicodeDecodeError; a saida com o assunto tambem estourava ao escrever num
pipe cp1252. Apareceu com o primeiro commit `🐛 ...` com [unlock:] (PR #10).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import CORE_LOCK


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class CheckLockUtf8Tests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.sb = Path(self._tmp.name)
        (self.sb / "core" / "lock").mkdir(parents=True)
        for name in ("lock_api.py", "check-lock.py"):
            shutil.copy2(CORE_LOCK / name, self.sb / "core" / "lock" / name)
        (self.sb / ".guia" / "locks").mkdir(parents=True)
        (self.sb / ".guia" / "locks" / "registry.yaml").write_text(
            "version: 1\nlocks:\n- id: homologado\n  description: d\n  operations: [modify]\n"
            "  files:\n  - x.txt\n",
            encoding="utf-8",
        )
        (self.sb / "x.txt").write_text("x\n", encoding="utf-8")
        for args in (
            ("init", "-q"),
            ("config", "user.email", "t@t"),
            ("config", "user.name", "t"),
            ("add", "."),
            ("commit", "-q", "-m", "🐛 fix(D-001): corrigir x\n\n[unlock:homologado] motivo: teste"),
        ):
            subprocess.run(["git", *args], cwd=self.sb, check=True, capture_output=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _check_lock(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "core/lock/check-lock.py", *args],
            cwd=self.sb, capture_output=True, text=True, encoding="utf-8",
        )

    def test_audit_json_reads_emoji_subject(self) -> None:
        result = self._check_lock("audit", "--json")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        subjects = [entry["subject"] for entry in json.loads(result.stdout)["unlocks"]]
        self.assertEqual(subjects, ["🐛 fix(D-001): corrigir x"])

    def test_audit_text_writes_emoji_subject(self) -> None:
        result = self._check_lock("audit")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("🐛 fix(D-001)", result.stdout)

    def test_history_reads_emoji_subject(self) -> None:
        result = self._check_lock("history", "homologado", "--json")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("🐛", result.stdout)


if __name__ == "__main__":
    unittest.main()
