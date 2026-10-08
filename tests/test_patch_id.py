"""D-127: o patch-id que carrega a auditoria nao pode ignorar espacos (R8).

`git patch-id --stable` descarta espaco em branco: mudar so a indentacao de
um bloco Python (o que muda o comportamento) daria o MESMO patch-id, e o
executor comentaria o marcador sozinho sobre codigo diferente do auditado.
O motor usa `--verbatim`.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from conftest_paths import ensure_core_importable

ensure_core_importable()

import _audit  # noqa: E402


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.autocrlf=false", *args],
        cwd=cwd, check=True, capture_output=True, text=True,
    ).stdout.strip()


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class PatchIdTests(unittest.TestCase):
    def test_indentation_change_changes_the_patch_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _git(repo, "init", "-q", "-b", "main")
            _git(repo, "commit", "-q", "--allow-empty", "-m", "base")
            _git(repo, "checkout", "-q", "-b", "v1")
            (repo / "m.py").write_text("if x:\n    a()\n    b()\n", encoding="utf-8")
            _git(repo, "add", "m.py")
            _git(repo, "commit", "-q", "-m", "v1")
            _git(repo, "checkout", "-q", "-b", "v2", "main")
            (repo / "m.py").write_text("if x:\n    a()\nb()\n", encoding="utf-8")
            _git(repo, "add", "m.py")
            _git(repo, "commit", "-q", "-m", "v2")
            first = _audit.patch_id(repo, "main", "v1")
            second = _audit.patch_id(repo, "main", "v2")
            self.assertTrue(first and second)
            self.assertNotEqual(first, second, "so a indentacao mudou, e em Python isso muda o comportamento")

    def test_same_content_on_a_new_base_keeps_the_patch_id(self) -> None:
        """O caso legitimo do R8: rebase limpo sobre uma base que andou."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _git(repo, "init", "-q", "-b", "main")
            (repo / "outro.txt").write_text("x\n", encoding="utf-8")
            _git(repo, "add", "outro.txt")
            _git(repo, "commit", "-q", "-m", "base")
            _git(repo, "checkout", "-q", "-b", "feature")
            (repo / "m.py").write_text("print('oi')\n", encoding="utf-8")
            _git(repo, "add", "m.py")
            _git(repo, "commit", "-q", "-m", "feature")
            before = _audit.patch_id(repo, "main", "feature")
            _git(repo, "checkout", "-q", "main")
            (repo / "outro.txt").write_text("y\n", encoding="utf-8")
            _git(repo, "commit", "-q", "-am", "main andou")
            _git(repo, "checkout", "-q", "feature")
            _git(repo, "rebase", "-q", "main")
            after = _audit.patch_id(repo, "main", "feature")
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
