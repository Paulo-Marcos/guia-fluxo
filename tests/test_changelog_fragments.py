"""D-121: CHANGELOG por fragmentos (R9).

Cada demanda escreve `changelog.d/D-NNN.<categoria>.md` no worktree (o
fragmento viaja no PR); `compile` junta tudo no `[Unreleased]` - ou fecha uma
versao - agrupado por categoria na ordem do Keep a Changelog, por id numerico,
preservando as entradas ja escritas, e apaga os fragmentos. Acaba com o
conflito de todo PR no mesmo topo do CHANGELOG.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import CORE_LOCK, CORE_SRC

CHANGELOG = """# Changelog

Formato baseado em Keep a Changelog.

## [Unreleased]

### Fixed
- **Antigo inline.** Entrada escrita direto no arquivo.

## [1.0.0] - 2026-01-01

### Added
- Primeira versao.
"""


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class ChangelogFragmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.sb = Path(self._tmp.name)
        (self.sb / "core" / "src").mkdir(parents=True)
        (self.sb / "core" / "lock").mkdir(parents=True)
        for src in CORE_SRC.glob("*.py"):
            if not src.name.startswith("__"):
                shutil.copy2(src, self.sb / "core" / "src" / src.name)
        shutil.copy2(CORE_LOCK / "lock_api.py", self.sb / "core" / "lock" / "lock_api.py")
        (self.sb / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=self.sb, check=True, capture_output=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "core/src/guia.py", *args],
            cwd=self.sb, capture_output=True, text=True, encoding="utf-8",
        )

    def _ok(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = self._run(*args)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def _fragments(self) -> list[str]:
        folder = self.sb / "changelog.d"
        return sorted(p.name for p in folder.glob("*.md")) if folder.is_dir() else []

    def test_add_picks_the_category_from_the_kind(self) -> None:
        self._ok("feature", "nova coisa")
        self._ok("bug", "conserto")
        self._ok("chore", "arrumacao")
        for task_id in ("D-001", "D-002", "D-003"):
            self._ok("changelog", "add", task_id, "--text", f"texto de {task_id}")
        self.assertEqual(self._fragments(), ["D-001.added.md", "D-002.fixed.md", "D-003.changed.md"])
        body = (self.sb / "changelog.d" / "D-001.added.md").read_text(encoding="utf-8")
        self.assertEqual(body, "- texto de D-001\n")

    def test_add_category_override_and_no_overwrite(self) -> None:
        self._ok("chore", "seguranca")
        self._ok("changelog", "add", "D-001", "--category", "Security", "--text", "a")
        self.assertEqual(self._fragments(), ["D-001.security.md"])
        self.assertNotEqual(self._run("changelog", "add", "D-001", "--category", "Security", "--text", "b").returncode, 0)
        self.assertEqual((self.sb / "changelog.d" / "D-001.security.md").read_text(encoding="utf-8"), "- a\n")

    def test_add_refuses_paths_outside_the_fragment_dir(self) -> None:
        """Categoria e pasta entram no caminho: nada pode sair de changelog.d/."""
        self._ok("chore", "x")
        result = self._run("changelog", "add", "D-001", "--category", "/../../fora", "--text", "a")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(self.sb.rglob("fora*")), [])
        process = self.sb / ".guia" / "process.json"
        process.write_text('{"delivery": {"changelog": {"dir": "../fora"}}}', encoding="utf-8")
        self.assertNotEqual(self._run("changelog", "add", "D-001", "--text", "a").returncode, 0)
        self.assertFalse((self.sb.parent / "fora").exists())

    def test_compile_merges_into_unreleased_keeping_inline_entries(self) -> None:
        folder = self.sb / "changelog.d"
        folder.mkdir()
        (folder / "D-010.fixed.md").write_text("- dez (D-010)\n", encoding="utf-8")
        (folder / "D-9.fixed.md").write_text("- nove (D-9)\n", encoding="utf-8")
        (folder / "D-011.added.md").write_text("- onze (D-011)\n", encoding="utf-8")
        self._ok("changelog", "compile")
        text = (self.sb / "CHANGELOG.md").read_text(encoding="utf-8")
        unreleased = text.split("## [Unreleased]")[1].split("## [1.0.0]")[0]
        self.assertLess(unreleased.index("### Added"), unreleased.index("### Fixed"))
        fixed = unreleased.split("### Fixed")[1]
        self.assertLess(fixed.index("Antigo inline"), fixed.index("nove"))
        self.assertLess(fixed.index("nove"), fixed.index("dez"), "ordem por id numerico")
        self.assertIn("- Primeira versao.", text, "versoes anteriores intactas")
        self.assertEqual(self._fragments(), [])

    def test_compile_with_version_closes_the_section(self) -> None:
        (self.sb / "changelog.d").mkdir()
        (self.sb / "changelog.d" / "D-001.added.md").write_text("- novo (D-001)\n", encoding="utf-8")
        self._ok("changelog", "compile", "--version", "1.1.0", "--date", "2026-10-08")
        text = (self.sb / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## [Unreleased]\n\n## [1.1.0] - 2026-10-08\n", text)
        released = text.split("## [1.1.0] - 2026-10-08")[1].split("## [1.0.0]")[0]
        self.assertIn("novo (D-001)", released)
        self.assertIn("Antigo inline", released)

    def test_compile_without_fragments_changes_nothing(self) -> None:
        self._ok("changelog", "compile")
        self.assertEqual((self.sb / "CHANGELOG.md").read_text(encoding="utf-8"), CHANGELOG)


if __name__ == "__main__":
    unittest.main()
