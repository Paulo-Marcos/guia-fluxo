"""D-207: as regras da medida do delta que a 3a auditoria achou sem teste.

Cada teste aqui segura uma linha de `_audit_delta.py` que uma mutacao podia
tirar sem a suite perceber: o `--text` (um `.gitattributes` com `-diff`
transformava 200 linhas em "Binary files differ"), o `--no-textconv`, a
checagem do codigo de saida do git e a regua "antes + depois" da regra da
metade do PR.
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


def _numbered(prefix: str, count: int) -> str:
    return "".join(f"{prefix}{i}\n" for i in range(count))


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class DeltaRulesTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _git(self.root, "init", "-q", "-b", "main")
        _git(self.root, "config", "core.autocrlf", "false")
        self._write("leia.txt", "base\n")
        self.base = self._commit()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write(self, path: str, text: str) -> None:
        (self.root / path).parent.mkdir(parents=True, exist_ok=True)
        (self.root / path).write_text(text, encoding="utf-8")

    def _commit(self) -> str:
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-q", "-m", "c")
        return _git(self.root, "rev-parse", "HEAD")

    def _plan(self, rejected: str, head: str) -> dict:
        previous = {"result": "rejected", "auditedSha": rejected, "auditedBase": self.base}
        return delta_plan(self.root, previous, {"head": head, "base": self.base}, {})

    def test_nested_gitattributes_without_diff_does_not_hide_a_rewrite(self) -> None:
        """`*.py -diff` aninhado: sem `--text`, 400 linhas reescritas mediriam como 1 binario."""
        self._write("pkg/.gitattributes", "*.py -diff\n")
        self._write("pkg/x.py", _numbered("a", 200))
        rejected = self._commit()
        self._write("pkg/x.py", _numbered("b", 200))
        plan = self._plan(rejected, self._commit())
        self.assertEqual(plan["mode"], "full")
        self.assertIn("delta grande", plan["reason"])

    def test_textconv_of_the_user_does_not_hide_a_change(self) -> None:
        """Um textconv que devolve sempre o mesmo texto esconderia a mudanca do arquivo."""
        self._write(".gitattributes", "*.dat diff=igual\n")
        self._write("dados.dat", "um\n")
        self.base = self._commit()
        _git(self.root, "config", "diff.igual.textconv", "echo igual #")
        self._write("dados.dat", "dois\n")
        rejected = self._commit()
        self._write("dados.dat", "tres\n")
        plan = self._plan(rejected, self._commit())
        self.assertEqual((plan["mode"], plan["files"]), ("delta", ["dados.dat"]))

    def test_git_exit_code_is_checked(self) -> None:
        """Git que sai com erro e stdout vazio nao vira 'nada mudou'."""
        self._write("leia.txt", "um\n")
        rejected = self._commit()
        self._write("leia.txt", "dois\n")
        head = self._commit()
        real_run = subprocess.run

        def run(args, *rest, **kwargs):
            if "diff" in args:
                return subprocess.CompletedProcess(args=args, returncode=128, stdout=b"", stderr=b"fatal")
            return real_run(args, *rest, **kwargs)

        with mock.patch.object(_audit_delta.subprocess, "run", run):
            plan = self._plan(rejected, head)
        self.assertEqual(plan["mode"], "full")
        self.assertIn("falhou", plan["reason"])

    def test_half_rule_measures_both_sides(self) -> None:
        """80 linhas tiradas de 200: e menos da metade de antes + depois (320), entao fica delta."""
        self._write("app.txt", _numbered("a", 200))
        rejected = self._commit()
        self._write("app.txt", _numbered("a", 120))
        plan = self._plan(rejected, self._commit())
        self.assertEqual((plan["mode"], plan["lines"]), ("delta", 80))

    def test_the_code_that_feeds_the_ruler_is_sensitive(self) -> None:
        paths = ["core/src/_audit.py", "plugins/guia/bin/_cli_audit.py", "core/src/_autonomy.py",
                 "plugins/guia/bin/_commit.py", "web/vitest.config.ts", "pkg/.gitattributes"]
        self.assertEqual(_sensitive(paths + ["core/src/_task_view.py"], {}), sorted(paths))


if __name__ == "__main__":
    unittest.main()
