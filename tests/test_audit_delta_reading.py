"""D-207: o que o `audit` manda o auditor ler mostra o conteudo, mesmo com `-diff`.

A medida ja le com `--text`, mas o `range-diff` (e o `git show`) respeitam
o `-diff` do `.gitattributes` e escondem a linha: o auditor leria "Binary
files differ" onde houve codigo. O `audit` e o comentario no PR apontam
tambem `git diff --text <head-velho> <head-novo>` - e esse comando mostra a
linha que o range-diff esconde.
"""

from __future__ import annotations

import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from conftest_paths import CORE_SRC

sys.path.insert(0, str(CORE_SRC))

from _audit import delta_header  # noqa: E402
from _audit_delta import delta_plan  # noqa: E402
from _cli_audit import _print_delta  # noqa: E402


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=", *args],
                            cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class DeltaReadingTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _git(self.root, "init", "-q", "-b", "main")
        _git(self.root, "config", "core.autocrlf", "false")
        (self.root / ".gitattributes").write_text("*.py -diff\n", encoding="utf-8")
        (self.root / "x.py").write_text("valor = 1\n", encoding="utf-8")
        self.base = self._commit()
        (self.root / "x.py").write_text("valor = 2\n", encoding="utf-8")
        self.rejected = self._commit()
        (self.root / "x.py").write_text("valor = 3  # escondido pelo -diff\n", encoding="utf-8")
        self.head = self._commit()
        previous = {"result": "rejected", "auditedSha": self.rejected, "auditedBase": self.base,
                    "findings": ["[CORRIGIR] x.py:1 - valor errado"]}
        self.previous = previous
        self.plan = delta_plan(self.root, previous, {"head": self.head, "base": self.base}, {})

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _commit(self) -> str:
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-q", "-m", "c")
        return _git(self.root, "rev-parse", "HEAD")

    def test_audit_points_to_a_text_diff_that_shows_the_hidden_line(self) -> None:
        self.assertEqual(self.plan["mode"], "delta")
        out = io.StringIO()
        with redirect_stdout(out):
            _print_delta(self.previous, self.plan)
        command = f"git diff --text --no-textconv --no-ext-diff {self.rejected} {self.head}"
        self.assertIn(command, out.getvalue())
        self.assertNotIn("escondido", _git(self.root, "diff", self.rejected, self.head))
        self.assertIn("+valor = 3  # escondido pelo -diff", _git(self.root, *command.split()[1:]))

    def test_full_audit_also_points_to_the_text_diff(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out):
            _print_delta(self.previous, {**self.plan, "mode": "full", "reason": "teste"})
        self.assertIn(f"git diff --text --no-textconv --no-ext-diff {self.rejected} {self.head}", out.getvalue())

    def test_pr_comment_header_carries_the_text_diff(self) -> None:
        self.assertIn(f"`git diff --text --no-textconv --no-ext-diff {self.rejected} {self.head}`", delta_header(self.plan))


if __name__ == "__main__":
    unittest.main()
