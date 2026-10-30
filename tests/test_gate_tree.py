"""D-182: o portao nao roda duas vezes sobre o mesmo conteudo.

`guia gate` roda `delivery.gate.full` no worktree e grava `HEAD^{tree}` em
`.guia/gate-passed.json`; o `ship` pula o portao quando o tree do HEAD ja
passou pelos mesmos comandos (`--rerun-gate` forca). Arvore suja nao grava.
O portao do teste conta as passadas com `git config --add guia.gateruns`.
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

COUNT_CMD = "git config --add guia.gateruns x"


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=", *args],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8",
    )


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class GateTreeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.engine = base / "plugin" / "bin"
        self.engine.mkdir(parents=True)
        for src in CORE_SRC.glob("*.py"):
            if not src.name.startswith("__"):
                shutil.copy2(src, self.engine / src.name)
        shutil.copy2(CORE_LOCK / "lock_api.py", self.engine / "lock_api.py")
        remote = base / "remote.git"
        self.main = base / "app"
        (self.main / ".guia").mkdir(parents=True)
        self.process = {
            "delivery": {
                "mode": "pr",
                "changelog": {"style": "fragments"},
                "gate": {"full": [COUNT_CMD]},
            }
        }
        self._write_process()
        (self.main / ".gitignore").write_text(".guia/*\n!.guia/process.json\n", encoding="utf-8")
        (self.main / "app.txt").write_text("app\n", encoding="utf-8")
        _git(base, "init", "-q", "--bare", str(remote))
        for args in (("init", "-q", "-b", "main"), ("add", "."), ("commit", "-q", "-m", "init"),
                     ("remote", "add", "origin", str(remote)), ("push", "-q", "-u", "origin", "main")):
            self.assertEqual(_git(self.main, *args).returncode, 0, msg=str(args))
        self.fixture = base / "gh.json"
        self.fixture.write_text(json.dumps({"__auth__": True}), encoding="utf-8")
        self._ok(self.main, "feature", "Mostrar a nota")
        self._ok(self.main, "worktree", "add", "D-001")
        self.wt = base / "app-worktrees" / "d001"
        self._commit("app.txt", "app com nota\n")
        self._ok(self.wt, "ready", "--file", "app.txt", "--request-test", "nota :: tests/test_nota.py")
        self._ok(self.wt, "changelog", "add", "--text", "Mostra a nota (D-001).")
        _git(self.wt, "add", "changelog.d")
        _git(self.wt, "commit", "-q", "-m", "fragmento")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write_process(self) -> None:
        (self.main / ".guia" / "process.json").write_text(json.dumps(self.process), encoding="utf-8")

    def _commit(self, name: str, content: str) -> None:
        (self.wt / name).write_text(content, encoding="utf-8")
        _git(self.wt, "add", name)
        _git(self.wt, "commit", "-q", "-m", name)

    def _run(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.engine / "guia.py"), *args],
            cwd=cwd, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "GUIA_GH_FIXTURE": str(self.fixture)},
        )

    def _ok(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        result = self._run(cwd, *args)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def _runs(self) -> int:
        out = _git(self.wt, "config", "--get-all", "guia.gateruns").stdout
        return len(out.split())

    def test_ship_skips_the_tree_the_gate_already_passed(self) -> None:
        self._ok(self.wt, "gate")
        self.assertEqual(self._runs(), 1)
        result = self._ok(self.wt, "ship", "--body", "x")
        self.assertEqual(self._runs(), 1, "o ship nao repete o portao no mesmo tree")
        self.assertIn("ja passou neste tree", result.stderr)
        again = self._ok(self.wt, "gate")
        self.assertIn("ja passou", again.stdout)
        self.assertEqual(self._runs(), 1)

    def test_new_content_runs_the_gate_again(self) -> None:
        self._ok(self.wt, "gate")
        self._commit("app.txt", "app com nota e data\n")
        self._ok(self.wt, "ship", "--body", "x")
        self.assertEqual(self._runs(), 2)
        self._ok(self.wt, "ship", "--body", "x")
        self.assertEqual(self._runs(), 2, "o ship grava o tree que passou nele")

    def test_rerun_gate_forces(self) -> None:
        self._ok(self.wt, "gate")
        self._ok(self.wt, "ship", "--body", "x", "--rerun-gate")
        self.assertEqual(self._runs(), 2)
        self._ok(self.wt, "gate", "--rerun")
        self.assertEqual(self._runs(), 3)

    def test_changed_gate_commands_run_again(self) -> None:
        self._ok(self.wt, "gate")
        self.process["delivery"]["gate"]["full"] = [COUNT_CMD, "git --version"]
        self._write_process()
        self._ok(self.wt, "ship", "--body", "x")
        self.assertEqual(self._runs(), 2)

    def test_dirty_tree_is_not_recorded(self) -> None:
        (self.wt / "app.txt").write_text("sujo\n", encoding="utf-8")
        result = self._ok(self.wt, "gate")
        self.assertIn("NAO gravado", result.stdout)
        self.assertFalse((self.main / ".guia" / "gate-passed.json").exists())

    def test_failing_gate_exits_nonzero_and_records_nothing(self) -> None:
        self.process["delivery"]["gate"]["full"] = ["git comando-que-nao-existe"]
        self._write_process()
        result = self._run(self.wt, "gate")
        self.assertEqual(result.returncode, 1)
        self.assertIn("comando-que-nao-existe", result.stderr)
        self.assertFalse((self.main / ".guia" / "gate-passed.json").exists())
        shipped = self._run(self.wt, "ship", "--body", "x")
        self.assertNotEqual(shipped.returncode, 0, "ship recusado sai com codigo != 0")


if __name__ == "__main__":
    unittest.main()
