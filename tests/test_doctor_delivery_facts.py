"""D-117: `doctor --delivery` coleta os fatos do projeto e do GitHub (R2).

Cada fato sai com a fonte (comando ou arquivo). O GitHub entra pelo
adaptador `_github.py`; nos testes, `GUIA_GH_FIXTURE` aponta um JSON com as
respostas do `gh api` (e `__auth__` para o `gh auth status`), sem rede.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import CORE_LOCK, CORE_SRC

AUDIT_WORKFLOW = """name: Auditoria
on:
  issue_comment:
    types: [created]
jobs:
  registrar:
    runs-on: ubuntu-latest
    steps:
      - run: gh api "repos/$REPO/statuses/$HEAD" -f state=success -f context="Auditoria registrada"
"""

CI_WORKFLOW = """name: tests
on: [pull_request]
jobs:
  tests:
    runs-on: ubuntu-latest
    steps:
      - run: pytest
  ci-ok:
    name: CI ok
    if: always()
    needs: [tests]
    runs-on: ubuntu-latest
    steps:
      - run: echo ok
"""

FIXTURE = {
    "__auth__": True,
    "repos/dono/app": {
        "allow_squash_merge": True,
        "allow_merge_commit": False,
        "allow_rebase_merge": False,
        "allow_auto_merge": False,
        "delete_branch_on_merge": True,
    },
    "repos/dono/app/branches/main/protection": {
        "required_status_checks": {"strict": True, "contexts": ["CI ok", "Auditoria registrada"]},
        "enforce_admins": {"enabled": True},
        "required_linear_history": {"enabled": True},
    },
}


def _seed_engine_flat(bin_dir: Path) -> None:
    bin_dir.mkdir(parents=True)
    for src in CORE_SRC.glob("*.py"):
        if not src.name.startswith("__"):
            shutil.copy2(src, bin_dir / src.name)
    shutil.copy2(CORE_LOCK / "lock_api.py", bin_dir / "lock_api.py")


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class DeliveryFactsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.engine = base / "plugin" / "bin"
        _seed_engine_flat(self.engine)
        self.repo = base / "app"
        workflows = self.repo / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "auditoria.yml").write_text(AUDIT_WORKFLOW, encoding="utf-8")
        (workflows / "tests.yml").write_text(CI_WORKFLOW, encoding="utf-8")
        (self.repo / "CHANGELOG.md").write_text(
            "# Changelog\n\nFormato baseado em [Keep a Changelog](https://keepachangelog.com/).\n\n## [Unreleased]\n",
            encoding="utf-8",
        )
        (self.repo / "VERSION").write_text("1.0.0\n", encoding="utf-8")
        (self.repo / ".guia").mkdir()
        (self.repo / ".guia" / "process.json").write_text("{}", encoding="utf-8")
        for args in (("init", "-q", "-b", "main"), ("remote", "add", "origin", "https://github.com/dono/app.git")):
            subprocess.run(["git", *args], cwd=self.repo, check=True, capture_output=True)
        self.fixture = base / "gh.json"
        self.fixture.write_text(json.dumps(FIXTURE), encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _facts(self, fixture: Path | None = None) -> dict[str, dict]:
        env = {**__import__("os").environ, "GUIA_GH_FIXTURE": str(fixture or self.fixture)}
        result = subprocess.run(
            [sys.executable, str(self.engine / "guia.py"), "doctor", "--delivery", "--json"],
            cwd=self.repo, capture_output=True, text=True, encoding="utf-8", env=env,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        return {fact["name"]: fact for fact in json.loads(result.stdout)["facts"]}

    def test_every_fact_has_a_source(self) -> None:
        facts = self._facts()
        for name in ("remote", "gh", "protection", "merge", "audit-workflow", "ci-aggregator",
                     "changelog", "release", "hooks"):
            self.assertIn(name, facts)
            self.assertTrue(facts[name]["source"], name)

    def test_github_facts(self) -> None:
        facts = self._facts()
        self.assertEqual(facts["remote"]["value"], "dono/app")
        self.assertEqual(facts["gh"]["value"], "autenticado")
        protection = facts["protection"]["value"]
        self.assertEqual(protection["checks"], ["CI ok", "Auditoria registrada"])
        self.assertTrue(protection["strict"])
        self.assertTrue(protection["enforceAdmins"])
        self.assertEqual(facts["merge"]["value"]["methods"], ["squash"])
        self.assertFalse(facts["merge"]["value"]["autoMerge"])

    def test_repository_facts(self) -> None:
        facts = self._facts()
        self.assertEqual(facts["audit-workflow"]["value"]["statusContext"], "Auditoria registrada")
        self.assertEqual(facts["ci-aggregator"]["value"], "CI ok")
        self.assertTrue(facts["changelog"]["value"]["unreleased"])
        self.assertTrue(facts["changelog"]["value"]["keepAChangelog"])
        self.assertEqual(facts["release"]["value"]["version"], "1.0.0")

    def test_unprotected_branch_and_no_auth(self) -> None:
        fixture = self.fixture.parent / "gh-sem.json"
        fixture.write_text(json.dumps({"__auth__": False}), encoding="utf-8")
        facts = self._facts(fixture)
        self.assertEqual(facts["gh"]["value"], "nao autenticado")
        self.assertIsNone(facts["protection"]["value"])
        self.assertIn("gh", facts["protection"]["note"])


if __name__ == "__main__":
    unittest.main()
