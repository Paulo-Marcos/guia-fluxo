"""D-115: doctor confere core.hooksPath na config comum e no config.worktree.

O hook `commit-msg` e a primeira linha de defesa das travas. Ele pode ficar
mudo sem ninguem ver: em 01/10 a `pr-audit` gravou `core.hooksPath = NUL` na
config comum do clone e o app do Claude copiou para cada worktree novo
(kaizen da D-851 no gerador-cortes). O doctor passa a avisar: hooks
desligados, pasta sem `commit-msg`, config.worktree divergente da comum, e
projeto com travas sem hook configurado. Aviso, nao falha (`--strict` promove).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import CORE_LOCK, CORE_SRC

NULL_DEVICE = "NUL" if os.name == "nt" else "/dev/null"


def _seed_engine_flat(bin_dir: Path) -> None:
    bin_dir.mkdir(parents=True)
    for src in CORE_SRC.glob("*.py"):
        if not src.name.startswith("__"):
            shutil.copy2(src, bin_dir / src.name)
    shutil.copy2(CORE_LOCK / "lock_api.py", bin_dir / "lock_api.py")


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
        cwd=cwd, check=True, capture_output=True,
    )


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class DoctorHooksPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.engine = base / "plugin" / "bin"
        _seed_engine_flat(self.engine)
        self.repo = base / "app"
        (self.repo / ".guia" / "locks").mkdir(parents=True)
        (self.repo / ".guia" / "process.json").write_text("{}", encoding="utf-8")
        (self.repo / ".guia" / "locks" / "registry.yaml").write_text("version: 1\nlocks: []\n", encoding="utf-8")
        (self.repo / ".githooks").mkdir()
        (self.repo / ".githooks" / "commit-msg").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        _git(self.repo, "init", "-q", "-b", "main")
        _git(self.repo, "add", ".")
        _git(self.repo, "-c", "core.hooksPath=", "commit", "-q", "-m", "init")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _doctor(self, cwd: Path, *flags: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.engine / "guia.py"), "doctor", *flags],
            cwd=cwd, capture_output=True, text=True, encoding="utf-8",
        )

    def test_healthy_hooks_path_has_no_warning(self) -> None:
        _git(self.repo, "config", "core.hooksPath", ".githooks")
        result = self._doctor(self.repo)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertNotIn("hooksPath", result.stderr)

    def test_null_hooks_path_warns_and_strict_fails(self) -> None:
        _git(self.repo, "config", "core.hooksPath", NULL_DEVICE)
        result = self._doctor(self.repo)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("hooks desligados", result.stderr)
        self.assertEqual(self._doctor(self.repo, "--strict").returncode, 1)

    def test_hooks_dir_without_commit_msg_warns(self) -> None:
        (self.repo / "vazio").mkdir()
        _git(self.repo, "config", "core.hooksPath", "vazio")
        result = self._doctor(self.repo)
        self.assertIn("commit-msg", result.stderr)

    def test_unset_with_locks_warns(self) -> None:
        result = self._doctor(self.repo)
        self.assertIn("core.hooksPath nao configurado", result.stderr)

    def test_worktree_config_diverging_from_common_warns(self) -> None:
        _git(self.repo, "config", "core.hooksPath", ".githooks")
        _git(self.repo, "config", "extensions.worktreeConfig", "true")
        worktree = self.repo.parent / "app-wt"
        _git(self.repo, "worktree", "add", "-q", str(worktree), "-b", "x")
        _git(worktree, "config", "--worktree", "core.hooksPath", NULL_DEVICE)
        result = self._doctor(worktree)
        self.assertIn("config.worktree", result.stderr)
        self.assertIn("hooks desligados", result.stderr)


if __name__ == "__main__":
    unittest.main()
