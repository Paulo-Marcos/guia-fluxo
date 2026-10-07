"""D-109: no modo `pr`, o estado mora na arvore principal (R3).

Com um worktree por demanda, o `.guia/` versionado do worktree tem so a
configuracao (o estado e local, fora do git). Rodado de dentro do worktree,
o motor achava esse `.guia/` e criava ali uma copia orfa do estado. No modo
`pr` ele passa a ler e gravar o `.guia/` da arvore principal; no `direct`
(padrao, sem `delivery`), nada muda.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import CORE_LOCK, CORE_SRC, ensure_core_importable

ensure_core_importable()

import _constants  # noqa: E402


def _seed_engine_flat(bin_dir: Path) -> None:
    """Motor fora do projeto, como no cache do plugin (raiz pelo CWD)."""
    bin_dir.mkdir(parents=True)
    for src in CORE_SRC.glob("*.py"):
        if not src.name.startswith("__"):
            shutil.copy2(src, bin_dir / src.name)
    shutil.copy2(CORE_LOCK / "lock_api.py", bin_dir / "lock_api.py")


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


def _repo_with_worktree(base: Path, process: dict) -> tuple[Path, Path]:
    """Repo com `.guia/process.json` versionado e um worktree ligado."""
    main = base / "main"
    (main / ".guia").mkdir(parents=True)
    (main / ".guia" / "process.json").write_text(json.dumps(process), encoding="utf-8")
    (main / ".gitignore").write_text(".guia/tasks.json\n.guia/backlog.json\n", encoding="utf-8")
    _git(main, "init", "-q", "-b", "main")
    _git(main, "add", ".")
    _git(main, "commit", "-q", "-m", "init")
    worktree = base / "main-d001"
    _git(main, "worktree", "add", "-q", str(worktree), "-b", "d-001-x")
    return main, worktree


def _run(engine: Path, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(engine / "guia.py"), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


class WorktreeStateRootTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.engine = self.base / "plugin" / "bin"
        _seed_engine_flat(self.engine)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_pr_mode_writes_state_in_main_tree(self) -> None:
        main, worktree = _repo_with_worktree(self.base, {"delivery": {"mode": "pr"}})
        result = _run(self.engine, worktree, "chore", "demanda no worktree")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue((main / ".guia" / "tasks.json").is_file())
        self.assertFalse(
            (worktree / ".guia" / "tasks.json").exists(),
            "copia orfa do estado nasceu no worktree",
        )

    def test_direct_mode_keeps_worktree_root(self) -> None:
        main, worktree = _repo_with_worktree(self.base, {"schemaVersion": 1})
        result = _run(self.engine, worktree, "chore", "demanda no worktree")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue((worktree / ".guia" / "tasks.json").is_file())
        self.assertFalse((main / ".guia" / "tasks.json").exists())

    def test_pr_mode_in_main_tree_is_unchanged(self) -> None:
        main, _ = _repo_with_worktree(self.base, {"delivery": {"mode": "pr"}})
        result = _run(self.engine, main, "chore", "demanda na principal")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue((main / ".guia" / "tasks.json").is_file())


class LinkedWorktreeMainTests(unittest.TestCase):
    def test_submodule_git_file_is_not_a_worktree(self) -> None:
        """`.git` arquivo sem `commondir` (submodulo) nao redireciona."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sub"
            gitdir = Path(tmp) / "parent" / ".git" / "modules" / "sub"
            gitdir.mkdir(parents=True)
            root.mkdir()
            (root / ".git").write_text(f"gitdir: {gitdir}\n", encoding="utf-8")
            self.assertIsNone(_constants._linked_worktree_main(root))

    def test_plain_repo_is_not_a_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            self.assertIsNone(_constants._linked_worktree_main(root))


if __name__ == "__main__":
    unittest.main()
