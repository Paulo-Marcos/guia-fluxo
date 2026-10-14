"""D-167: o ship so aceita marca [unlock:] que sobrevive ao rebase da fila.

O `update-branch --rebase` do GitHub descarta commit vazio e merge. Uma marca
so neles some e o lock-check do PR reprova depois (D-157, PR #49). O ship
confere antes de qualquer efeito - e antes do portao, para a recusa ser rapida.
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

REGISTRY = """version: 1
locks:
- id: testes-sao-contrato
  description: testes sao contrato
  operations: [modify, delete]
  files:
  - tests/*
"""


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=", *args],
                          cwd=cwd, capture_output=True, text=True, encoding="utf-8")


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class ShipUnlockMarkTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.engine = base / "plugin" / "bin"
        self.engine.mkdir(parents=True)
        for src in CORE_SRC.glob("*.py"):
            if not src.name.startswith("__"):
                shutil.copy2(src, self.engine / src.name)
        shutil.copy2(CORE_LOCK / "lock_api.py", self.engine / "lock_api.py")
        shutil.copytree(REPO_ROOT / "core" / "templates", base / "plugin" / "templates")
        remote = base / "remote.git"
        self.main = base / "app"
        (self.main / ".guia" / "locks").mkdir(parents=True)
        (self.main / ".guia" / "locks" / "registry.yaml").write_text(REGISTRY, encoding="utf-8")
        # Portao que falharia: a recusa por marca tem de vir antes dele.
        (self.main / ".guia" / "process.json").write_text(json.dumps({"delivery": {
            "mode": "pr", "commit": {"format": "gitmoji-conventional"},
            "gate": {"full": ["git rev-parse --verify nao-existe"]}}}), encoding="utf-8")
        (self.main / ".gitignore").write_text(".guia/*\n!.guia/process.json\n!.guia/locks/\n", encoding="utf-8")
        (self.main / "tests").mkdir()
        (self.main / "tests" / "test_x.py").write_text("x = 1\n", encoding="utf-8")
        _git(base, "init", "-q", "--bare", str(remote))
        for args in (("init", "-q", "-b", "main"), ("add", "."), ("commit", "-q", "-m", "init"),
                     ("remote", "add", "origin", str(remote)), ("push", "-q", "-u", "origin", "main")):
            self.assertEqual(_git(self.main, *args).returncode, 0, msg=str(args))
        self.fixture = base / "gh.json"
        self.fixture.write_text(json.dumps({"__auth__": True}), encoding="utf-8")
        self._ok(self.main, "chore", "Ajustar o teste")
        self._ok(self.main, "worktree", "add", "D-001")
        self.wt = base / "app-d001"
        self._ok(self.wt, "ready", "--file", "tests/test_x.py", "--request-test", "x :: tests/test_x.py")
        (self.wt / "tests" / "test_x.py").write_text("x = 2\n", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(self.engine / "guia.py"), *args], cwd=cwd, capture_output=True,
                              text=True, encoding="utf-8",
                              env={**os.environ, "GUIA_GH_FIXTURE": str(self.fixture), "CLAUDE_PLUGIN_ROOT": ""})

    def _ok(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        result = self._run(cwd, *args)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def _ship(self) -> subprocess.CompletedProcess[str]:
        return self._run(self.wt, "ship", "--no-changelog", "teste", "--body", "porque",
                         "--unlock-reason", "testes-sao-contrato=autorizado no teste")

    def test_mark_only_in_an_empty_commit_is_refused_before_the_gate(self) -> None:
        _git(self.wt, "commit", "-q", "-am", "ajusta o teste")  # sem a marca
        _git(self.wt, "commit", "-q", "--allow-empty", "-m", "x\n\n[unlock:testes-sao-contrato] motivo: m")
        result = self._ship()
        self.assertNotEqual(result.returncode, 0)
        out = result.stdout + result.stderr
        self.assertIn("testes-sao-contrato", out)
        self.assertIn("Commit vazio ou merge some no rebase", out)
        self.assertNotIn("portao falhou", out, "a recusa vem antes do portao")

    def test_mark_in_the_commit_that_touches_the_file_passes_this_check(self) -> None:
        _git(self.wt, "commit", "-q", "-am", "ajusta o teste\n\n[unlock:testes-sao-contrato] motivo: m")
        out = self._ship().stdout + self._ship().stderr
        self.assertNotIn("Commit vazio ou merge some no rebase", out)
        self.assertIn("portao falhou", out, "passou da conferencia das marcas e chegou ao portao")

    def test_emoji_in_the_history_does_not_break_the_check(self) -> None:
        # O git devolve UTF-8; lido no codec do Windows (cp1252) o byte 0x90 do 🐛 derrubava o ship.
        _git(self.wt, "commit", "-q", "-am", "🐛 ajusta o teste — çã\n\n[unlock:testes-sao-contrato] motivo: m")
        out = self._ship().stdout + self._ship().stderr
        self.assertNotIn("Traceback", out)
        self.assertIn("portao falhou", out)


if __name__ == "__main__":
    unittest.main()
