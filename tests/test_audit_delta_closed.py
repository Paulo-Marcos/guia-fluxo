"""D-207: a medida do delta falha fechada.

Duas auditorias seguidas acharam um caso novo que a medida nao via (ordem,
` b/`, nome fora de UTF-8, submodulo). Em vez de um teste por caso, o
contrato: tudo o que a medida nao entende - nome que nao e UTF-8, arquivo
listado com patch vazio, linha de cabecalho desconhecida, git que falha -
vira auditoria completa, com o motivo. Os testes injetam cada falha na saida
do git, sem depender de o sistema de arquivos aceitar o caso.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from conftest_paths import CORE_SRC

sys.path.insert(0, str(CORE_SRC))

import _audit_delta  # noqa: E402
from _audit_delta import _sensitive, delta_plan  # noqa: E402


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=", *args],
                            cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class FailClosedTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _git(self.root, "init", "-q", "-b", "main")
        _git(self.root, "config", "core.autocrlf", "false")
        (self.root / "app.txt").write_text("um\n", encoding="utf-8")
        self.base = self._commit()
        (self.root / "app.txt").write_text("dois\n", encoding="utf-8")
        self.rejected = self._commit()
        (self.root / "app.txt").write_text("tres\n", encoding="utf-8")
        self.head = self._commit()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _commit(self) -> str:
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-q", "--allow-empty", "-m", "c")
        return _git(self.root, "rev-parse", "HEAD")

    def _plan(self) -> dict:
        previous = {"result": "rejected", "auditedSha": self.rejected, "auditedBase": self.base}
        return delta_plan(self.root, previous, {"head": self.head, "base": self.base}, {})

    def _with_git_output(self, rewrite) -> dict:
        """Roda a medida com a saida do git reescrita por `rewrite(args, saida)`."""
        real = _audit_delta._git_bytes

        def fake(root: Path, *args: str) -> bytes:
            return rewrite(args, real(root, *args))

        with mock.patch.object(_audit_delta, "_git_bytes", fake):
            return self._plan()

    def test_baseline_is_a_delta(self) -> None:
        self.assertEqual(self._plan()["mode"], "delta")

    def test_name_outside_utf8_goes_full(self) -> None:
        plan = self._with_git_output(lambda args, out: out + b".github/\xff/action.yml\x00" if "--name-only" in args else out)
        self.assertEqual(plan["mode"], "full")
        self.assertIn("UTF-8", plan["reason"])

    def test_listed_file_with_empty_patch_goes_full(self) -> None:
        plan = self._with_git_output(lambda args, out: b"" if "--unified=0" in args else out)
        self.assertEqual(plan["mode"], "full")
        self.assertIn("patch veio vazio", plan["reason"])

    def test_unknown_header_line_goes_full(self) -> None:
        plan = self._with_git_output(
            lambda args, out: out.replace(b"index ", b"similarity index 90%\nindex ", 1) if "--unified=0" in args else out)
        self.assertEqual(plan["mode"], "full")
        self.assertIn("nao reconhecida", plan["reason"])

    def test_git_failure_goes_full(self) -> None:
        def fail(root: Path, *args: str) -> bytes:
            raise _audit_delta.Unmeasurable("git diff falhou")

        with mock.patch.object(_audit_delta, "_git_bytes", fail):
            self.assertEqual(self._plan()["mode"], "full")

    def test_trailing_newline_only_is_measured(self) -> None:
        """O head reprovado tem `tres\\n`; a correcao so tira a quebra final."""
        self.rejected = self.head
        (self.root / "app.txt").write_bytes(b"tres")
        self.head = self._commit()
        self.assertEqual(self._plan()["files"], ["app.txt"])

    def test_submodule_is_seen_even_when_config_hides_it(self) -> None:
        _git(self.root, "config", "diff.ignoreSubmodules", "all")
        _git(self.root, "update-index", "--add", "--cacheinfo", f"160000,{self.base},sub")
        _git(self.root, "commit", "-q", "-m", "submodulo")
        self.head = _git(self.root, "rev-parse", "HEAD")
        self.assertIn("sub", self._plan()["files"])

    def test_locks_config_and_the_ruler_itself_are_sensitive(self) -> None:
        paths = [".guia/process.json", "docs/AGENTS.md", "core/src/_audit_delta.py", "core/lock/check-lock.py",
                 "plugins/guia/bin/_locks.py", ".claude-plugin/marketplace.json", "core/build/render-skills.py",
                 "pytest.ini", "web/.npmrc", "bun.lockb"]
        self.assertEqual(_sensitive(paths + ["docs/guia.md"], {}), sorted(paths))


if __name__ == "__main__":
    unittest.main()
