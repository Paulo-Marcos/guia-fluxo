"""D-119: perfis de entrega, propostos pelos fatos e aplicados so com pedido (R2).

`solo-direct` (sem remoto GitHub ou sem CI/protecao), `pr-basic` (CI, sem
auditoria por status) e `pr-audited` (workflow de auditoria). O perfil so
preenche chaves que o motor ja usa. `guia profile` propoe; `--apply` grava o
bloco `delivery` no process.json sem sobrescrever o que ja existe.
"""

from __future__ import annotations

import json
import os
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

GH = {
    "__auth__": True,
    "repos/dono/app": {"allow_squash_merge": True},
    "repos/dono/app/branches/main/protection": {
        "required_status_checks": {"strict": True, "contexts": ["CI ok"]},
        "enforce_admins": {"enabled": True},
    },
}


def _seed_engine_flat(bin_dir: Path) -> None:
    bin_dir.mkdir(parents=True)
    for src in CORE_SRC.glob("*.py"):
        if not src.name.startswith("__"):
            shutil.copy2(src, bin_dir / src.name)
    shutil.copy2(CORE_LOCK / "lock_api.py", bin_dir / "lock_api.py")


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class DeliveryProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.engine = self.base / "plugin" / "bin"
        _seed_engine_flat(self.engine)
        self.repo = self.base / "app"
        self.workflows = self.repo / ".github" / "workflows"
        self.workflows.mkdir(parents=True)
        (self.workflows / "tests.yml").write_text(CI_WORKFLOW, encoding="utf-8")
        (self.workflows / "auditoria.yml").write_text(AUDIT_WORKFLOW, encoding="utf-8")
        (self.repo / ".guia").mkdir()
        self.process = self.repo / ".guia" / "process.json"
        self.process.write_text(json.dumps({"projectName": "app"}), encoding="utf-8")
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=self.repo, check=True, capture_output=True)
        self.fixture = self.base / "gh.json"
        self.fixture.write_text(json.dumps(GH), encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _add_remote(self) -> None:
        subprocess.run(["git", "remote", "add", "origin", "https://github.com/dono/app.git"],
                       cwd=self.repo, check=True, capture_output=True)

    def _profile(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(self.engine / "guia.py"), "profile", *args],
            cwd=self.repo, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "GUIA_GH_FIXTURE": str(self.fixture)},
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        return result

    def _proposed(self) -> str:
        return json.loads(self._profile("--json").stdout)["profile"]

    def _delivery(self) -> dict:
        return json.loads(self.process.read_text(encoding="utf-8")).get("delivery", {})

    def test_audit_workflow_proposes_pr_audited(self) -> None:
        self._add_remote()
        self.assertEqual(self._proposed(), "pr-audited")

    def test_ci_without_audit_proposes_pr_basic(self) -> None:
        self._add_remote()
        (self.workflows / "auditoria.yml").unlink()
        self.assertEqual(self._proposed(), "pr-basic")

    def test_no_remote_proposes_solo_direct(self) -> None:
        self.assertEqual(self._proposed(), "solo-direct")

    def test_proposing_does_not_write(self) -> None:
        self._add_remote()
        self._profile()
        self.assertEqual(self._delivery(), {})

    def test_apply_writes_only_known_keys(self) -> None:
        self._add_remote()
        self._profile("--apply")
        self.assertEqual(self._delivery(), {
            "mode": "pr",
            "commit": {"format": "gitmoji-conventional"},
            "audit": {"statusContext": "Auditoria registrada"},
        })
        self.assertEqual(json.loads(self.process.read_text(encoding="utf-8"))["projectName"], "app")

    def test_apply_never_overwrites_existing_keys(self) -> None:
        self._add_remote()
        self.process.write_text(json.dumps({"delivery": {"commit": {"format": "legacy"}}}), encoding="utf-8")
        result = self._profile("--apply")
        self.assertEqual(self._delivery()["commit"]["format"], "legacy")
        self.assertEqual(self._delivery()["mode"], "pr")
        self.assertIn("delivery.commit.format", result.stdout)

    def test_apply_named_profile(self) -> None:
        self._add_remote()
        self._profile("--apply", "--name", "solo-direct")
        self.assertEqual(self._delivery(), {"mode": "direct"})

    def test_doctor_delivery_shows_the_proposal(self) -> None:
        self._add_remote()
        result = subprocess.run(
            [sys.executable, str(self.engine / "guia.py"), "doctor", "--delivery", "--json"],
            cwd=self.repo, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "GUIA_GH_FIXTURE": str(self.fixture)},
        )
        self.assertEqual(json.loads(result.stdout)["profile"]["name"], "pr-audited")


if __name__ == "__main__":
    unittest.main()
