"""D-202, auditoria do PR #96: a faxina nao pode propor o que nao e dela.

- Arquivo solto era qualquer arquivo da pasta pai: num projeto dentro da
  pasta do usuario, `--remove all` apagaria `.gitconfig` e documentos.
- `--remove all` re-varria a pasta e levava arquivo que o dono nao viu.
- `--remove ""` casava o primeiro worktree sem demanda.
- Worktree sem demanda em branch recem-criada parecia "contida na base".
- Arquivo ignorado (`.env`) nao contava como mudanca local, e o
  `git worktree remove` o apaga junto.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import test_cleanup_parent_folder as base
from test_cleanup_parent_folder import _git


class CleanupAuditFixesTests(unittest.TestCase):
    setUp = base.CleanupParentFolderTests.setUp
    tearDown = base.CleanupParentFolderTests.tearDown
    _run = base.CleanupParentFolderTests._run
    _ok = base.CleanupParentFolderTests._ok
    _finished_worktree = base.CleanupParentFolderTests._finished_worktree

    def test_only_agent_artifacts_count_as_loose_files(self) -> None:
        """Projeto dentro da pasta do usuario: `.gitconfig` e documento nunca sao propostos."""
        for name in (".gitconfig", ".claude.json", "Contrato.docx", "proj.code-workspace", "README.md", "notas.md"):
            (self.dev / name).write_text("x\n", encoding="utf-8")
        artifacts = ["v12.txt", "d963-audit.md", "gate-backend.log", "null", "vm.txt", "npmaud-fe.json",
                     "g-build.rc", "g-build.txt"]
        for name in artifacts:
            (self.dev / name).write_text("x\n", encoding="utf-8")
        report = json.loads(self._ok("cleanup", "--json").stdout)
        self.assertEqual(sorted(Path(f["path"]).name for f in report["files"]), sorted(artifacts))
        self._ok("cleanup", "--remove", "all")
        self.assertTrue((self.dev / ".gitconfig").exists())
        self.assertTrue((self.dev / "Contrato.docx").exists())

    def test_remove_all_takes_only_what_was_listed(self) -> None:
        (self.dev / "v1.txt").write_text("x\n", encoding="utf-8")
        self.assertNotEqual(self._run("cleanup", "--remove", "all").returncode, 0, "sem listagem antes")
        self._ok("cleanup")
        (self.dev / "v2.txt").write_text("x\n", encoding="utf-8")  # depois da lista
        self._ok("cleanup", "--remove", "all")
        self.assertFalse((self.dev / "v1.txt").exists())
        self.assertTrue((self.dev / "v2.txt").exists(), "o dono nao viu este")

    def test_empty_target_removes_nothing(self) -> None:
        worktree = self._finished_worktree()
        self.assertNotEqual(self._run("cleanup", "--remove", "").returncode, 0)
        self.assertTrue(worktree.is_dir())

    def test_worktree_without_demand_is_not_proposed(self) -> None:
        """Branch recem-criada tambem 'esta contida na base'."""
        fresh = self.dev / "app-solta"
        self.assertEqual(_git(self.main, "worktree", "add", "-q", str(fresh), "-b", "experimento").returncode, 0)
        report = json.loads(self._ok("cleanup", "--json").stdout)
        self.assertEqual(report["worktrees"], [])

    def test_ignored_file_in_worktree_keeps_it(self) -> None:
        """`git worktree remove` apaga arquivo ignorado (`.env`) sem perguntar."""
        worktree = self._finished_worktree()
        (worktree / ".gitignore").write_text(".guia/*\n!.guia/process.json\n.env\n", encoding="utf-8")
        _git(worktree, "add", ".gitignore")
        _git(worktree, "commit", "-q", "-m", "ignora .env")
        (worktree / ".env").write_text("SEGREDO=1\n", encoding="utf-8")
        report = json.loads(self._ok("cleanup", "--json").stdout)
        self.assertEqual(report["worktrees"], [])
        self.assertIn(".env", report["kept"][0]["why"])


if __name__ == "__main__":
    unittest.main()
