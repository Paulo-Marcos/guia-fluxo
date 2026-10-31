"""D-207: a medida do delta nao deixa passar o que muda o que o PR faz.

A regra "delta sensivel volta a auditoria completa" depende de saber quais
arquivos o delta tocou e quanto. Rename puro, modo do arquivo, binario, linhas
trocadas de lugar e caminho com ` b/` no meio nao aparecem numa conta ingenua
de linhas `+`/`-`: cada um tem um teste aqui.
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

    def _write(self, path: str, text: str) -> None:
        (self.root / path).parent.mkdir(parents=True, exist_ok=True)
        (self.root / path).write_text(text, encoding="utf-8")

    def _commit(self, message: str = "muda") -> str:
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-q", "-m", message)
        return _git(self.root, "rev-parse", "HEAD")

    def _plan(self, config: dict | None = None) -> dict:
        """Head reprovado = o commit anterior; o delta e so o ultimo commit."""
        rejected = _git(self.root, "rev-parse", "HEAD~1")
        previous = {"result": "rejected", "auditedSha": rejected, "auditedBase": self.base}
        return delta_plan(self.root, previous, {"head": _git(self.root, "rev-parse", "HEAD"), "base": self.base},
                          config or {})

    def test_moving_a_workflow_counts_the_workflow(self) -> None:
        _git(self.root, "mv", ".github/workflows/ci.yml", "ci-desligado.yml")
        self.assertIn(".github/workflows/ci.yml", _file_patches(self.root, self.base, self._commit()))

    def test_removed_sql_comment_is_content_not_header(self) -> None:
        self._write("app.sql", "select 1;\n")
        self.assertEqual(_file_patches(self.root, self.base, self._commit())["app.sql"], ["--- comentario"])

    def test_binary_change_counts(self) -> None:
        (self.root / "logo.bin").write_bytes(b"\x00\x01\x02")
        self.assertTrue(any(line.startswith("binary ") for line in
                            _file_patches(self.root, self.base, self._commit())["logo.bin"]))

    def test_accented_path_is_measured_by_its_name(self) -> None:
        self._write(".github/workflows/ação.yml", "on: push\n")
        self.assertIn(".github/workflows/ação.yml", _file_patches(self.root, self.base, self._commit()))

    def test_rename_of_a_workflow_after_rejection_goes_full(self) -> None:
        """O delta todo e um rename: sem `--no-renames` ele teria zero linhas e passaria como delta."""
        self._write("app.sql", "-- comentario\nselect 2;\n")
        self._commit()
        _git(self.root, "mv", ".github/workflows/ci.yml", "ci-desligado.yml")
        self._commit()
        plan = self._plan()
        self.assertEqual(plan["mode"], "full")
        self.assertIn(".github/workflows/ci.yml", plan["reason"])

    def test_swapping_two_workflow_lines_goes_full(self) -> None:
        """A ordem importa: trocar duas linhas de lugar muda o que o workflow faz."""
        self._write(".github/workflows/ci.yml", "on: push\na: permissions: read-all\nb: permissions: write-all\n")
        self._commit()
        self._write(".github/workflows/ci.yml", "on: push\nb: permissions: write-all\na: permissions: read-all\n")
        self._commit()
        plan = self._plan()
        self.assertEqual((plan["mode"], plan["lines"]), ("full", 2))
        self.assertIn(".github/workflows/ci.yml", plan["reason"])

    def test_path_with_b_slash_inside_is_not_cut(self) -> None:
        """`.github/actions/x b/action.yml`: o cabecalho do diff cortaria no ` b/` errado."""
        self._write("app.sql", "-- comentario\nselect 2;\n")
        self._commit()
        self._write(".github/actions/x b/action.yml", "runs: {using: composite}\n")
        self._commit()
        self.assertIn(".github/actions/x b/action.yml", self._plan()["reason"])

    def test_mode_change_alone_counts(self) -> None:
        self._write("run.sh", "echo oi\n")
        self._commit()
        _git(self.root, "update-index", "--chmod=+x", "run.sh")
        _git(self.root, "commit", "-q", "-m", "executavel")
        plan = self._plan()
        self.assertEqual((plan["mode"], plan["files"]), ("delta", ["run.sh"]))

    def test_agents_md_matches_in_any_case(self) -> None:
        self._write("app.sql", "-- comentario\nselect 2;\n")
        self._commit()
        self._write("AGENTS.md", "# regras\n")
        self._commit()
        self.assertIn("AGENTS.md", self._plan()["reason"])

    def test_always_human_pattern_matches_in_any_case(self) -> None:
        """Padrao do dono em caixa mista casa no Linux (o fnmatch de la diferencia caixa)."""
        self._write("app.sql", "-- comentario\nselect 2;\n")
        self._commit()
        self._write("docs/x.md", "x\n")
        self._commit()
        self.assertIn("docs/x.md", self._plan({"autonomy": {"alwaysHuman": ["Docs/**"]}})["reason"])

    def test_new_unlock_mark_goes_full(self) -> None:
        self._write("app.sql", "-- comentario\nselect 2;\n")
        self._commit()
        self._write("app.sql", "-- comentario\nselect 3;\n")
        self._commit("corrige\n\n[unlock:travado] motivo: x")
        self.assertIn("[unlock:] novo: travado", self._plan()["reason"])

    def test_delta_over_half_of_the_pr_goes_full(self) -> None:
        self._write("app.py", "".join(f"a{i}\n" for i in range(60)))
        self._commit()
        self._write("app.py", "".join(f"b{i}\n" for i in range(60)))
        self._commit()
        self.assertIn("mais da metade do PR", self._plan({"delivery": {"audit": {"deltaMaxLines": 1000}}})["reason"])

    @unittest.skipIf(sys.platform == "win32", "o Windows nao aceita aspas no nome do arquivo")
    def test_quoted_path_is_measured_by_its_name(self) -> None:
        self._write('a"b.txt', "x\n")
        self.assertIn('a"b.txt', _file_patches(self.root, self.base, self._commit()))


if __name__ == "__main__":
    unittest.main()
