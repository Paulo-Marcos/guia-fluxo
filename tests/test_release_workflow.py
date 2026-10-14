"""D-174: o workflow de release publica as notas do CHANGELOG e nao falha se o Release ja existe.

Na 0.8.0 o Release foi criado a mao (com as notas do CHANGELOG) segundos antes
do workflow, que tentou cria-lo de novo com notas dos commits e falhou com
"tag already exists". A tag passa a ser o unico gatilho: o passo de notas tira
a secao da versao do CHANGELOG.md, e o de publicacao cria ou so atualiza. O
teste roda o `run:` do proprio workflow, nao uma copia dele.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

from conftest_paths import REPO_ROOT

WORKFLOW = REPO_ROOT / ".github" / "workflows" / "release.yml"
NOTES_STEP = "Notas da versao a partir do CHANGELOG"
PUBLISH_STEP = "Publicar o GitHub Release"

CHANGELOG = """# Changelog

## [Unreleased]

## [1.2.0] - 2026-10-14

### Added
- novo comando (D-002)

### Fixed
- defeito (D-003)

## [1.1.0] - 2026-10-01

### Added
- antigo (D-001)
"""


def _bash() -> str | None:
    """O bash do Git no Windows (o `bash` do PATH pode ser o do WSL); no resto, o do PATH."""
    git = shutil.which("git")
    if os.name == "nt" and git:
        return next((str(parent / "bin" / "bash.exe") for parent in Path(git).parents
                     if (parent / "bin" / "bash.exe").is_file()), None)
    return shutil.which("bash")


BASH = _bash()


def _step(name: str) -> dict:
    jobs = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]
    return next(step for job in jobs.values() for step in job.get("steps", []) if step.get("name") == name)


@unittest.skipUnless(BASH, "bash (do Git) necessario")
class ReleaseNotesStepTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _notes(self, tag: str, changelog: str, version: str | None = None) -> subprocess.CompletedProcess[str]:
        (self.dir / "CHANGELOG.md").write_text(changelog, encoding="utf-8", newline="\n")
        (self.dir / "VERSION").write_text((version or tag.removeprefix("v")) + "\n", encoding="utf-8")
        script = self.dir / "step.sh"
        script.write_text(_step(NOTES_STEP)["run"], encoding="utf-8", newline="\n")
        return subprocess.run([BASH, "-e", str(script)], cwd=self.dir, capture_output=True, text=True,
                              encoding="utf-8", env={**os.environ, "TAG": tag})

    def test_takes_only_the_section_of_the_tag(self) -> None:
        result = self._notes("v1.2.0", CHANGELOG)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        notes = (self.dir / "release-notes.md").read_text(encoding="utf-8")
        self.assertIn("novo comando (D-002)", notes)
        self.assertIn("defeito (D-003)", notes)
        self.assertNotIn("antigo (D-001)", notes, "para na versao seguinte")
        self.assertNotIn("## [", notes)

    def test_missing_section_fails_with_the_fix(self) -> None:
        result = self._notes("v9.9.9", CHANGELOG)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("changelog compile --version 9.9.9", result.stderr)

    def test_tag_must_match_the_version_file(self) -> None:
        result = self._notes("v1.2.0", CHANGELOG, version="1.1.0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("nao bate com o VERSION", result.stderr)

    def test_the_real_changelog_has_the_current_version(self) -> None:
        version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
        result = self._notes(f"v{version}", (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))
        self.assertEqual(result.returncode, 0, msg=result.stderr)


class PublishStepTests(unittest.TestCase):
    def test_creates_or_only_updates_and_never_generates_notes(self) -> None:
        run = _step(PUBLISH_STEP)["run"]
        self.assertIn('gh release view "$TAG"', run)
        self.assertIn('gh release edit "$TAG" --notes-file release-notes.md', run)
        self.assertIn('gh release create "$TAG" --title "$TAG" --notes-file release-notes.md', run)
        self.assertNotIn("--generate-notes", run)


if __name__ == "__main__":
    unittest.main()
