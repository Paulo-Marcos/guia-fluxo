"""D-120: andaimes de entrega gerados de core/templates/ (R2 + R11).

`guia scaffold <alvo>` cria `auditoria`, `pr-template` e `dependabot` a partir
de modelos do Guia, sem sobrescrever arquivo existente; `ci-ok` e
`protection` so imprimem (o job depende dos jobs do projeto; mudar o GitHub e
acao externa do dono).
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

import yaml

from conftest_paths import CORE_LOCK, CORE_SRC, REPO_ROOT

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


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class ScaffoldTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.engine = base / "plugin" / "bin"
        self.engine.mkdir(parents=True)
        for src in CORE_SRC.glob("*.py"):
            if not src.name.startswith("__"):
                shutil.copy2(src, self.engine / src.name)
        shutil.copy2(CORE_LOCK / "lock_api.py", self.engine / "lock_api.py")
        shutil.copytree(REPO_ROOT / "core" / "templates", base / "plugin" / "templates")
        self.repo = base / "app"
        (self.repo / ".github" / "workflows").mkdir(parents=True)
        (self.repo / ".github" / "workflows" / "tests.yml").write_text(CI_WORKFLOW, encoding="utf-8")
        (self.repo / ".guia").mkdir()
        (self.repo / ".guia" / "process.json").write_text(json.dumps({"delivery": {
            "mode": "pr",
            "commit": {"format": "gitmoji-conventional"},
            "audit": {"statusContext": "Auditoria ok"},
        }}), encoding="utf-8")
        for args in (("init", "-q", "-b", "main"), ("remote", "add", "origin", "https://github.com/dono/app.git")):
            subprocess.run(["git", *args], cwd=self.repo, check=True, capture_output=True)
        self.fixture = base / "gh.json"
        self.fixture.write_text(json.dumps({"__auth__": True}), encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _scaffold(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.engine / "guia.py"), "scaffold", *args],
            cwd=self.repo, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "GUIA_GH_FIXTURE": str(self.fixture), "CLAUDE_PLUGIN_ROOT": ""},
        )

    def _ok(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = self._scaffold(*args)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        return result

    def _untracked(self) -> list[str]:
        out = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"],
                             cwd=self.repo, capture_output=True, text=True).stdout
        return sorted(line[3:] for line in out.splitlines())

    def test_auditoria_uses_the_configured_context(self) -> None:
        self._ok("auditoria")
        path = self.repo / ".github" / "workflows" / "auditoria.yml"
        text = path.read_text(encoding="utf-8")
        self.assertIn('context="Auditoria ok"', text)
        self.assertIn("auditoria-aprovada sha=", text)
        data = yaml.safe_load(text)
        self.assertIn("issue_comment", data.get("on", data.get(True)))

    def test_never_overwrites(self) -> None:
        path = self.repo / ".github" / "workflows" / "auditoria.yml"
        path.write_text("meu\n", encoding="utf-8")
        result = self._scaffold("auditoria")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(path.read_text(encoding="utf-8"), "meu\n")

    def test_pr_template_has_request_to_test_table(self) -> None:
        self._ok("pr-template")
        text = (self.repo / ".github" / "pull_request_template.md").read_text(encoding="utf-8")
        self.assertIn("Pedido", text)
        self.assertIn("Teste", text)

    def test_pr_template_respects_other_casing(self) -> None:
        (self.repo / ".github" / "PULL_REQUEST_TEMPLATE.md").write_text("antigo\n", encoding="utf-8")
        self.assertNotEqual(self._scaffold("pr-template").returncode, 0)
        # No Windows (sem distincao de caixa) os dois nomes sao o mesmo arquivo:
        # a prova que vale nos dois sistemas e o conteudo antigo intacto.
        names = [p.name for p in (self.repo / ".github").iterdir() if p.suffix == ".md"]
        self.assertEqual(names, ["PULL_REQUEST_TEMPLATE.md"])
        self.assertEqual(
            (self.repo / ".github" / "PULL_REQUEST_TEMPLATE.md").read_text(encoding="utf-8"), "antigo\n"
        )

    def test_dependabot_uses_the_commit_prefix(self) -> None:
        self._ok("dependabot")
        data = yaml.safe_load((self.repo / ".github" / "dependabot.yml").read_text(encoding="utf-8"))
        update = data["updates"][0]
        self.assertEqual(update["package-ecosystem"], "github-actions")
        self.assertEqual(update["commit-message"]["prefix"], "🧹 chore")

    def test_ci_ok_and_protection_only_print(self) -> None:
        before = self._untracked()
        ci_ok = self._ok("ci-ok").stdout
        self.assertIn("if: always()", ci_ok)
        protection = self._ok("protection").stdout
        self.assertIn("repos/dono/app/branches/main/protection", protection)
        self.assertIn('"CI ok"', protection)
        self.assertIn('"Auditoria ok"', protection)
        self.assertEqual(self._untracked(), before, "ci-ok e protection nao gravam nada")

    def test_ci_ok_needs_only_jobs_of_one_workflow(self) -> None:
        """`needs` nao enxerga job de outro workflow: listar um quebraria o CI."""
        (self.repo / ".github" / "workflows" / "lock-check.yml").write_text(
            "name: lock-check\non: [pull_request]\njobs:\n  lock-check:\n    runs-on: ubuntu-latest\n"
            "    steps:\n      - run: echo ok\n",
            encoding="utf-8",
        )
        out = self._ok("ci-ok").stdout
        needs_line = next(line for line in out.splitlines() if line.strip().startswith("needs:"))
        self.assertEqual(needs_line.strip(), "needs: [tests]")
        self.assertIn("lock-check", out, "os jobs de outros workflows aparecem na nota")


if __name__ == "__main__":
    unittest.main()
