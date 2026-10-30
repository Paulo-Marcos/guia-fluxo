"""D-207: a medida do delta nao deixa passar o que nao tem linha `+`/`-`.

A regra "delta sensivel volta a auditoria completa" depende de saber quais
arquivos o delta tocou. Rename puro, modo do arquivo, binario e caminho que o
git poe entre aspas nao tem linha de conteudo: sem cuidado, sumiriam da conta.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import CORE_SRC

sys.path.insert(0, str(CORE_SRC))

from _audit_delta import _file_patches, delta_plan  # noqa: E402


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=", *args],
                            cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class FilePatchesTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _git(self.root, "init", "-q", "-b", "main")
        _git(self.root, "config", "core.autocrlf", "false")
        (self.root / ".github" / "workflows").mkdir(parents=True)
        (self.root / ".github" / "workflows" / "ci.yml").write_text("on: push\njobs: {}\n", encoding="utf-8")
        (self.root / "app.sql").write_text("-- comentario\nselect 1;\n", encoding="utf-8")
        _git(self.root, "add", ".")
        _git(self.root, "commit", "-q", "-m", "base")
        self.base = _git(self.root, "rev-parse", "HEAD")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _commit(self) -> str:
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-q", "-m", "muda")
        return _git(self.root, "rev-parse", "HEAD")

    def test_moving_a_workflow_counts_the_workflow(self) -> None:
        _git(self.root, "mv", ".github/workflows/ci.yml", "ci-desligado.yml")
        patches = _file_patches(self.root, self.base, self._commit())
        self.assertIn(".github/workflows/ci.yml", patches)

    def test_removed_sql_comment_is_content_not_header(self) -> None:
        (self.root / "app.sql").write_text("select 1;\n", encoding="utf-8")
        patches = _file_patches(self.root, self.base, self._commit())
        self.assertEqual(patches["app.sql"], {"--- comentario": 1})

    def test_binary_change_counts(self) -> None:
        (self.root / "logo.bin").write_bytes(b"\x00\x01\x02")
        patches = _file_patches(self.root, self.base, self._commit())
        self.assertTrue(any(key.startswith("binary ") for key in patches["logo.bin"]))

    def test_accented_path_is_measured_by_its_name(self) -> None:
        """`core.quotePath=false`: acento nao poe o caminho entre aspas, e ele nao cai na conta do anterior."""
        (self.root / ".github" / "workflows" / "ação.yml").write_text("on: push\n", encoding="utf-8")
        patches = _file_patches(self.root, self.base, self._commit())
        self.assertIn(".github/workflows/ação.yml", patches)

    @unittest.skipIf(sys.platform == "win32", "o Windows nao aceita aspas no nome do arquivo")
    def test_quoted_path_is_not_measured(self) -> None:
        (self.root / 'a"b.txt').write_text("x\n", encoding="utf-8")
        self.assertIsNone(_file_patches(self.root, self.base, self._commit()))

    def test_rename_of_a_workflow_after_rejection_goes_full(self) -> None:
        """O delta todo e um rename: sem `--no-renames` ele teria zero linhas e passaria como delta."""
        (self.root / "app.sql").write_text("-- comentario\nselect 2;\n", encoding="utf-8")
        rejected = self._commit()
        _git(self.root, "mv", ".github/workflows/ci.yml", "ci-desligado.yml")
        head = self._commit()
        previous = {"result": "rejected", "auditedSha": rejected, "auditedBase": self.base}
        plan = delta_plan(self.root, previous, {"head": head, "base": self.base}, {})
        self.assertEqual(plan["mode"], "full")
        self.assertIn(".github/workflows/ci.yml", plan["reason"])


if __name__ == "__main__":
    unittest.main()
