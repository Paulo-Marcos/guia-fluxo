"""D-113: worktree da demanda por modelo, com juncoes criadas e desfeitas pelo motor.

No modo `pr`, `guia worktree add D-NNN` cria `..\\{repo}-{idCompact}` na
branch `{idLower}-{slug}` a partir de `origin/{baseBranch}`, copia os
`envFiles` e cria as `junctions` declaradas (juncao no Windows, link simbolico
no resto) apontando para a arvore principal. `guia worktree remove` desfaz as
juncoes antes de remover o worktree e recusa remover se sobrar qualquer link:
em 05/10 um `git worktree remove --force` atravessou uma juncao e apagou o
`node_modules` da arvore principal (D-880 no gerador-cortes).
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


def _seed_engine_flat(bin_dir: Path) -> None:
    bin_dir.mkdir(parents=True)
    for src in CORE_SRC.glob("*.py"):
        if not src.name.startswith("__"):
            shutil.copy2(src, bin_dir / src.name)
    shutil.copy2(CORE_LOCK / "lock_api.py", bin_dir / "lock_api.py")


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=", *args],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8",
    )


def _make_link(link: Path, target: Path) -> None:
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], check=True, capture_output=True)
    else:
        os.symlink(target, link, target_is_directory=True)


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class WorktreeTemplateTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.engine = base / "plugin" / "bin"
        _seed_engine_flat(self.engine)
        self.main = base / "app"
        remote = base / "remote.git"
        (self.main / ".guia").mkdir(parents=True)
        (self.main / ".guia" / "process.json").write_text(json.dumps({
            "delivery": {
                "mode": "pr",
                "worktree": {"envFiles": [".env.local"], "junctions": ["deps"]},
            }
        }), encoding="utf-8")
        (self.main / ".gitignore").write_text(
            ".guia/*\n!.guia/process.json\ndeps/\n.env.local\n", encoding="utf-8"
        )
        (self.main / "app.txt").write_text("app\n", encoding="utf-8")
        _git(base, "init", "-q", "--bare", str(remote))
        for args in (("init", "-q", "-b", "main"), ("add", "."), ("commit", "-q", "-m", "init"),
                     ("remote", "add", "origin", str(remote)), ("push", "-q", "origin", "main")):
            self.assertEqual(_git(self.main, *args).returncode, 0, msg=str(args))
        (self.main / "deps").mkdir()
        (self.main / "deps" / "pacote.txt").write_text("compartilhado\n", encoding="utf-8")
        (self.main / ".env.local").write_text("API=local\n", encoding="utf-8")
        self._ok("chore", "Nota e porquê com junções")
        self.worktree = base / "app-d001"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.engine / "guia.py"), *args],
            cwd=self.main, capture_output=True, text=True, encoding="utf-8",
        )

    def _ok(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = self._run(*args)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def test_add_follows_templates_with_env_and_junction(self) -> None:
        self._ok("worktree", "add", "D-001")
        self.assertTrue(self.worktree.is_dir())
        branch = _git(self.worktree, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        self.assertEqual(branch, "d-001-nota-e-porque-com-juncoes")
        self.assertEqual((self.worktree / ".env.local").read_text(encoding="utf-8"), "API=local\n")
        self.assertEqual((self.worktree / "deps" / "pacote.txt").read_text(encoding="utf-8"), "compartilhado\n")
        task = json.loads((self.main / ".guia" / "tasks.json").read_text(encoding="utf-8"))["tasks"][0]
        self.assertEqual(task["worktree"]["junctions"], ["deps"])

    def test_remove_undoes_junction_and_keeps_main_intact(self) -> None:
        self._ok("worktree", "add", "D-001")
        self._ok("worktree", "remove", "D-001")
        self.assertFalse(self.worktree.exists())
        self.assertEqual(
            (self.main / "deps" / "pacote.txt").read_text(encoding="utf-8"),
            "compartilhado\n",
            "a remocao atravessou a juncao e apagou a pasta da principal (D-880)",
        )

    def test_remove_refuses_with_undeclared_link(self) -> None:
        self._ok("worktree", "add", "D-001")
        _make_link(self.worktree / "atalho", self.main / "deps")
        result = self._run("worktree", "remove", "D-001")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("atalho", result.stdout + result.stderr)
        self.assertTrue(self.worktree.exists())
        self.assertTrue((self.main / "deps" / "pacote.txt").exists())

    def test_remove_refuses_dirty_worktree_without_force(self) -> None:
        self._ok("worktree", "add", "D-001")
        (self.worktree / "app.txt").write_text("mudado\n", encoding="utf-8")
        result = self._run("worktree", "remove", "D-001")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--force", result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertTrue(self.worktree.exists())

    def test_add_refuses_paths_outside_the_worktree(self) -> None:
        process = self.main / ".guia" / "process.json"
        data = json.loads(process.read_text(encoding="utf-8"))
        data["delivery"]["worktree"]["junctions"] = ["../fora"]
        process.write_text(json.dumps(data), encoding="utf-8")
        result = self._run("worktree", "add", "D-001")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("'../fora'", result.stdout + result.stderr)
        self.assertFalse(self.worktree.exists(), "recusa antes de criar o worktree")


if __name__ == "__main__":
    unittest.main()
