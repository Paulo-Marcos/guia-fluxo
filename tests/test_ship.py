"""D-122: `guia ship` leva a demanda do worktree ao PR (R3/R4).

Confere o modo `pr`, a arvore limpa, a tabela Pedido -> Teste, o fragmento de
CHANGELOG e o portao completo; empurra a branch, abre (ou atualiza) o PR com o
titulo do commit e o corpo montado da demanda, grava a mensagem de squash e
poe a demanda em `Em PR`. O `gh` entra pelo adaptador: com GUIA_GH_FIXTURE,
os PRs ficam num arquivo ao lado (`<fixture>.prs.json`).
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
class ShipTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.engine = base / "plugin" / "bin"
        self.engine.mkdir(parents=True)
        for src in CORE_SRC.glob("*.py"):
            if not src.name.startswith("__"):
                shutil.copy2(src, self.engine / src.name)
        shutil.copy2(CORE_LOCK / "lock_api.py", self.engine / "lock_api.py")
        self.remote = base / "remote.git"
        self.main = base / "app"
        (self.main / ".guia").mkdir(parents=True)
        self.process = {
            "delivery": {
                "mode": "pr",
                "commit": {"format": "gitmoji-conventional", "coAuthor": "Agente <a@b>"},
                "changelog": {"style": "fragments"},
                "gate": {"full": ["git --version"]},
                "pr": {"footer": "Gerado pelo agente"},
            }
        }
        self._write_process()
        (self.main / ".gitignore").write_text(".guia/*\n!.guia/process.json\n", encoding="utf-8")
        (self.main / "app.txt").write_text("app\n", encoding="utf-8")
        _git(base, "init", "-q", "--bare", str(self.remote))
        for args in (("init", "-q", "-b", "main"), ("add", "."), ("commit", "-q", "-m", "init"),
                     ("remote", "add", "origin", str(self.remote)), ("push", "-q", "-u", "origin", "main")):
            self.assertEqual(_git(self.main, *args).returncode, 0, msg=str(args))
        self.fixture = base / "gh.json"
        self.fixture.write_text(json.dumps({"__auth__": True}), encoding="utf-8")
        self._ok(self.main, "feature", "Mostrar a nota")
        self._ok(self.main, "worktree", "add", "D-001")
        self.wt = base / "app-d001"
        (self.wt / "app.txt").write_text("app com nota\n", encoding="utf-8")
        _git(self.wt, "add", "app.txt")
        _git(self.wt, "commit", "-q", "-m", "nota")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write_process(self) -> None:
        (self.main / ".guia" / "process.json").write_text(json.dumps(self.process), encoding="utf-8")

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

    def _ready(self) -> None:
        self._ok(self.wt, "ready", "--file", "app.txt", "--request-test", "mostrar a nota :: tests/test_nota.py")
        self._ok(self.wt, "changelog", "add", "--text", "Mostra a nota (D-001).")
        _git(self.wt, "add", "changelog.d")
        _git(self.wt, "commit", "-q", "-m", "fragmento")

    def _task(self) -> dict:
        return json.loads((self.main / ".guia" / "tasks.json").read_text(encoding="utf-8"))["tasks"][0]

    def _prs(self) -> list[dict]:
        path = Path(str(self.fixture) + ".prs.json")
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []

    def test_ship_opens_the_pr_and_moves_to_em_pr(self) -> None:
        self._ready()
        self._ok(self.wt, "ship", "--body", "Porque o aluno precisa ver a nota.")
        heads = _git(self.main, "ls-remote", "--heads", "origin").stdout
        self.assertIn("d-001-mostrar-a-nota", heads, "branch empurrada")
        prs = self._prs()
        self.assertEqual(len(prs), 1)
        self.assertEqual(prs[0]["title"], "✨ feat(D-001): Mostrar a nota")
        body = prs[0]["body"]
        for piece in ("Porque o aluno precisa ver a nota.", "| mostrar a nota | tests/test_nota.py |",
                      "Demanda: D-001", "Gerado pelo agente"):
            self.assertIn(piece, body)
        task = self._task()
        self.assertEqual(task["status"], "Em PR")
        self.assertEqual(task["pr"]["number"], prs[0]["number"])
        message = (self.main / ".guia" / "queue" / "D-001.msg").read_text(encoding="utf-8")
        self.assertTrue(message.startswith("✨ feat(D-001): Mostrar a nota"))
        self.assertIn("Co-Authored-By: Agente <a@b>", message)

    def test_second_ship_updates_the_same_pr(self) -> None:
        self._ready()
        self._ok(self.wt, "ship", "--body", "v1")
        self._ok(self.wt, "ship", "--body", "v2")
        prs = self._prs()
        self.assertEqual(len(prs), 1)
        self.assertIn("v2", prs[0]["body"])

    def test_refuses_without_request_to_test(self) -> None:
        self._ok(self.wt, "changelog", "add", "--text", "x")
        _git(self.wt, "add", "changelog.d")
        _git(self.wt, "commit", "-q", "-m", "fragmento")
        result = self._run(self.wt, "ship", "--body", "x")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Pedido", result.stdout + result.stderr)
        self.assertEqual(self._prs(), [])

    def test_refuses_without_fragment_unless_reason(self) -> None:
        self._ok(self.wt, "ready", "--file", "app.txt", "--request-test", "a :: b")
        result = self._run(self.wt, "ship", "--body", "x")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("changelog", (result.stdout + result.stderr).lower())
        self._ok(self.wt, "ship", "--body", "x", "--no-changelog", "mudanca so interna")
        self.assertIn("mudanca so interna", self._prs()[0]["body"])

    def test_refuses_dirty_tree(self) -> None:
        self._ready()
        (self.wt / "app.txt").write_text("sujo\n", encoding="utf-8")
        result = self._run(self.wt, "ship", "--body", "x")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self._prs(), [])

    def test_refuses_when_the_gate_fails(self) -> None:
        self.process["delivery"]["gate"]["full"] = ["git comando-que-nao-existe"]
        self._write_process()
        self._ready()
        result = self._run(self.wt, "ship", "--body", "x")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("comando-que-nao-existe", result.stdout + result.stderr)
        self.assertEqual(self._prs(), [])
        self.assertNotEqual(self._task()["status"], "Em PR")

    def test_direct_mode_refuses(self) -> None:
        self._ready()
        self.process["delivery"]["mode"] = "direct"
        self._write_process()
        result = self._run(self.main, "ship", "D-001", "--body", "x")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("modo pr", result.stdout + result.stderr)
        self.assertEqual(self._prs(), [])


if __name__ == "__main__":
    unittest.main()
