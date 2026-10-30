"""D-202, reauditoria do PR #96 (head 6cae280): duas brechas de perda de dados.

- A regra de rascunho (`.txt`/`.md`/`.json` com digito ou nome curto) ainda
  propunha documento real: `IRPF2025.txt`, `tsconfig.json`, `cv.md`.
- O nome de uma juncao gravada valia como "nada a perder" mesmo quando a
  juncao tinha virado pasta real - o `git worktree remove` a apagaria.
"""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

import test_cleanup_parent_folder as base
from test_cleanup_parent_folder import _git


class CleanupAuditRound2Tests(unittest.TestCase):
    setUp = base.CleanupParentFolderTests.setUp
    tearDown = base.CleanupParentFolderTests.tearDown
    _run = base.CleanupParentFolderTests._run
    _ok = base.CleanupParentFolderTests._ok
    _finished_worktree = base.CleanupParentFolderTests._finished_worktree

    def test_real_documents_with_numbers_or_short_names_are_never_proposed(self) -> None:
        for name in ("tsconfig.json", "relatorio2025.md", "IRPF2025.txt", "cv.md", "cidade.txt",
                     "projeto-123456-abc.json", "senhas1.txt"):
            (self.dev / name).write_text("x\n", encoding="utf-8")
        for name in ("d975-files.txt", "auditoria-d976-r2.md", "c968b.txt", "msg968.txt", "ship957.txt"):
            (self.dev / name).write_text("x\n", encoding="utf-8")
        report = json.loads(self._ok("cleanup", "--json").stdout)
        self.assertEqual(
            sorted(Path(f["path"]).name for f in report["files"]),
            sorted(["d975-files.txt", "auditoria-d976-r2.md", "c968b.txt", "msg968.txt", "ship957.txt"]),
        )

    def _worktree_with_junction(self) -> Path:
        process = self.main / ".guia" / "process.json"
        process.write_text(json.dumps({"delivery": {"mode": "pr", "worktree": {"junctions": ["uploads"]}}}),
                           encoding="utf-8")
        (self.main / ".gitignore").write_text(".guia/*\n!.guia/process.json\nuploads/\n", encoding="utf-8")
        for args in (("add", ".gitignore"), ("commit", "-q", "-m", "ignora uploads"), ("push", "-q", "origin", "main")):
            self.assertEqual(_git(self.main, *args).returncode, 0, msg=str(args))
        (self.main / "uploads").mkdir()
        (self.main / "uploads" / "foto.jpg").write_text("principal\n", encoding="utf-8")
        return self._finished_worktree()

    def test_intact_junction_does_not_hold_the_worktree(self) -> None:
        worktree = self._worktree_with_junction()
        report = json.loads(self._ok("cleanup", "--json").stdout)
        self.assertEqual([Path(w["path"]).name for w in report["worktrees"]], [worktree.name])

    def test_junction_replaced_by_a_real_folder_keeps_the_worktree(self) -> None:
        worktree = self._worktree_with_junction()
        link = worktree / "uploads"
        os.rmdir(link) if os.name == "nt" else os.unlink(link)
        link.mkdir()
        (link / "foto.jpg").write_text("so no worktree\n", encoding="utf-8")
        report = json.loads(self._ok("cleanup", "--json").stdout)
        self.assertEqual(report["worktrees"], [])
        self.assertIn("uploads", report["kept"][0]["why"])

    def test_detached_head_keeps_the_worktree(self) -> None:
        worktree = self._finished_worktree()
        self.assertEqual(_git(worktree, "checkout", "-q", "--detach").returncode, 0)
        report = json.loads(self._ok("cleanup", "--json").stdout)
        self.assertEqual(report["worktrees"], [])
        self.assertIn("HEAD destacado", report["kept"][0]["why"])


if __name__ == "__main__":
    unittest.main()
