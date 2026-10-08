"""D-118: `doctor --delivery` acusa deriva entre a configuracao e o GitHub (R2).

No modo `pr`, os fatos da D-117 sao comparados com o que o processo precisa:
protecao na base, auditoria exigida (e com o mesmo contexto da config),
`CI ok` exigido, `strict`, `enforce_admins`, squash ligado e auto-merge
desligado. Cada deriva vira aviso (`--strict` reprova) e sai no JSON em
`drift`. No modo `direct`, nada a comparar.
"""

from __future__ import annotations

import copy
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

HEALTHY = {
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
PROTECTION = "repos/dono/app/branches/main/protection"


def _seed_engine_flat(bin_dir: Path) -> None:
    bin_dir.mkdir(parents=True)
    for src in CORE_SRC.glob("*.py"):
        if not src.name.startswith("__"):
            shutil.copy2(src, bin_dir / src.name)
    shutil.copy2(CORE_LOCK / "lock_api.py", bin_dir / "lock_api.py")


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class DeliveryDriftTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.engine = self.base / "plugin" / "bin"
        _seed_engine_flat(self.engine)
        self.repo = self.base / "app"
        workflows = self.repo / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "auditoria.yml").write_text(AUDIT_WORKFLOW, encoding="utf-8")
        (workflows / "tests.yml").write_text(CI_WORKFLOW, encoding="utf-8")
        (self.repo / ".guia").mkdir()
        self._process({"delivery": {"mode": "pr"}})
        for args in (("init", "-q", "-b", "main"), ("remote", "add", "origin", "https://github.com/dono/app.git")):
            subprocess.run(["git", *args], cwd=self.repo, check=True, capture_output=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _process(self, data: dict) -> None:
        (self.repo / ".guia" / "process.json").write_text(json.dumps(data), encoding="utf-8")

    def _doctor(self, gh: dict, *flags: str) -> subprocess.CompletedProcess[str]:
        fixture = self.base / "gh.json"
        fixture.write_text(json.dumps(gh), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(self.engine / "guia.py"), "doctor", "--delivery", *flags],
            cwd=self.repo, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "GUIA_GH_FIXTURE": str(fixture)},
        )

    def _drift(self, gh: dict) -> list[str]:
        result = self._doctor(gh, "--json")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        return json.loads(result.stdout)["drift"]

    def test_healthy_setup_has_no_drift(self) -> None:
        self.assertEqual(self._drift(HEALTHY), [])

    def test_audit_status_not_required(self) -> None:
        gh = copy.deepcopy(HEALTHY)
        gh[PROTECTION]["required_status_checks"]["contexts"] = ["CI ok"]
        drift = self._drift(gh)
        self.assertTrue(any("Auditoria registrada" in d and "sem auditoria" in d for d in drift), drift)

    def test_ci_aggregator_not_required(self) -> None:
        gh = copy.deepcopy(HEALTHY)
        gh[PROTECTION]["required_status_checks"]["contexts"] = ["Auditoria registrada"]
        self.assertTrue(any("CI ok" in d for d in self._drift(gh)))

    def test_no_protection(self) -> None:
        gh = copy.deepcopy(HEALTHY)
        del gh[PROTECTION]
        self.assertTrue(any("sem protecao" in d for d in self._drift(gh)))

    def test_loose_protection_and_merge_settings(self) -> None:
        gh = copy.deepcopy(HEALTHY)
        gh[PROTECTION]["required_status_checks"]["strict"] = False
        gh[PROTECTION]["enforce_admins"]["enabled"] = False
        gh["repos/dono/app"]["allow_auto_merge"] = True
        gh["repos/dono/app"]["allow_squash_merge"] = False
        drift = " | ".join(self._drift(gh))
        for marker in ("strict", "enforce_admins", "auto-merge", "squash"):
            self.assertIn(marker, drift)

    def test_configured_context_differs_from_workflow(self) -> None:
        self._process({"delivery": {"mode": "pr", "audit": {"statusContext": "Auditoria ok"}}})
        drift = self._drift(HEALTHY)
        self.assertTrue(any("Auditoria ok" in d and "Auditoria registrada" in d for d in drift), drift)

    def test_drift_is_a_warning_and_strict_fails(self) -> None:
        gh = copy.deepcopy(HEALTHY)
        gh["repos/dono/app"]["allow_auto_merge"] = True
        result = self._doctor(gh)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("warn: deriva", result.stderr)
        self.assertEqual(self._doctor(gh, "--strict").returncode, 1)

    def test_direct_mode_has_nothing_to_compare(self) -> None:
        self._process({})
        gh = copy.deepcopy(HEALTHY)
        del gh[PROTECTION]
        self.assertEqual(self._drift(gh), [])


if __name__ == "__main__":
    unittest.main()
