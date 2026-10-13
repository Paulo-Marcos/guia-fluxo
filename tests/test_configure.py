"""D-143: o motor do configurador (epico E-008).

`guia configure` monta o plano - cada etapa com a explicacao, o que o Guia viu
no projeto, as opcoes, a recomendada e o status (`nova`, `padrao`, `ok`,
`difere`) - e grava so o process.json, com backup, quando `--set` vem com
`--yes`. Sem `--yes` e simulacao. Etapas que dependem de outras (portao,
worktree, auditoria: so no modo pr) seguem as respostas ja dadas.
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
    permissions:
      statuses: write
    steps:
      - run: gh api repos/x/statuses/sha -f state=success -f context="Auditoria registrada"
"""


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=", *args],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8",
    )


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class ConfigureTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.main = base / "app"
        (self.main / "core" / "src").mkdir(parents=True)
        (self.main / "core" / "lock").mkdir(parents=True)
        for src in CORE_SRC.glob("*.py"):
            if not src.name.startswith("__"):
                shutil.copy2(src, self.main / "core" / "src" / src.name)
        shutil.copy2(CORE_LOCK / "lock_api.py", self.main / "core" / "lock" / "lock_api.py")
        (self.main / ".guia").mkdir()
        self.process = self.main / ".guia" / "process.json"
        self.process.write_text(json.dumps({"projectName": "app"}), encoding="utf-8")
        (self.main / ".gitignore").write_text(".guia/\ncore/\n", encoding="utf-8")
        (self.main / "app.txt").write_text("app\n", encoding="utf-8")
        for args in (("init", "-q", "-b", "main"), ("add", "."), ("commit", "-q", "-m", "init")):
            self.assertEqual(_git(self.main, *args).returncode, 0, msg=str(args))
        self.fixture = base / "gh.json"
        self.fixture.write_text(json.dumps({"__auth__": True}), encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "core/src/guia.py", "configure", *args],
            cwd=self.main, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "GUIA_GH_FIXTURE": str(self.fixture)},
        )

    def _ok(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = self._run(*args)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def _plan(self, *sets: str) -> dict[str, dict]:
        args = ["--plan", "--json"] + [arg for value in sets for arg in ("--set", value)]
        return {step["id"]: step for step in json.loads(self._ok(*args).stdout)["steps"]}

    def _config(self) -> dict:
        return json.loads(self.process.read_text(encoding="utf-8"))

    def _make_github_project(self) -> None:
        _git(self.main, "remote", "add", "origin", "https://github.com/dono/app.git")
        (self.main / ".github" / "workflows").mkdir(parents=True)
        (self.main / ".github" / "workflows" / "auditoria.yml").write_text(AUDIT_WORKFLOW, encoding="utf-8")

    def test_every_step_explains_itself(self) -> None:
        plan = self._plan()
        self.assertGreaterEqual(len(plan), 10)
        for step in plan.values():
            self.assertTrue(step["explain"].strip(), step["id"])
            self.assertTrue(step["recommendedWhy"].strip(), step["id"])
            self.assertIn(step["status"], ("nova", "padrao", "ok", "difere"))

    def test_recommendation_follows_the_project_facts(self) -> None:
        self.assertEqual(self._plan()["mode"]["recommended"], "direct", "sem remoto: nao ha onde abrir PR")
        self._make_github_project()
        plan = self._plan()
        self.assertEqual(plan["mode"]["recommended"], "pr")
        self.assertIn("pr-audited", plan["mode"]["recommendedWhy"])
        self.assertEqual(self._plan("mode=pr")["audit-status"]["recommended"], "Auditoria registrada")

    def test_pr_only_steps_follow_the_answers(self) -> None:
        self.assertFalse(self._plan()["gate"]["applies"], "modo direct: sem portao do ship")
        plan = self._plan("mode=pr")
        for step_id in ("gate", "worktree-junctions", "audit-status", "base-branch"):
            self.assertTrue(plan[step_id]["applies"], step_id)

    def test_set_without_yes_only_simulates(self) -> None:
        out = self._ok("--set", "mode=pr").stdout
        self.assertIn("delivery.mode", out)
        self.assertIn("Simulacao", out)
        self.assertNotIn("delivery", self._config())

    def test_yes_writes_with_backup(self) -> None:
        before = self.process.read_text(encoding="utf-8")
        result = json.loads(self._ok("--set", "mode=pr", "--set", "gate=python -m pytest -q, npm test",
                                     "--yes", "--json").stdout)
        self.assertTrue(result["written"])
        config = self._config()
        self.assertEqual(config["delivery"]["mode"], "pr")
        self.assertEqual(config["delivery"]["gate"]["full"], ["python -m pytest -q", "npm test"])
        self.assertEqual(config["projectName"], "app", "o resto do process.json fica")
        self.assertEqual(Path(result["backup"]).read_text(encoding="utf-8"), before)

    def test_special_values(self) -> None:
        self._ok("--set", "mode=pr", "--set", "commit-coauthor=Fulano <f@x>", "--set", "skills-audit=nenhuma", "--yes")
        config = self._config()
        self.assertEqual(config["skills"]["audit"], [])
        self.assertEqual(config["delivery"]["commit"]["coAuthor"], "Fulano <f@x>")
        self._ok("--set", "commit-coauthor=padrao", "--yes")
        self.assertNotIn("coAuthor", self._config()["delivery"].get("commit", {}))

    def test_bad_answers_are_refused(self) -> None:
        self.assertIn("nao e uma opcao", self._run("--set", "mode=talvez").stderr)
        self.assertIn("Etapa desconhecida", self._run("--set", "cor=azul").stderr)
        self.assertNotIn("delivery", self._config())

    def test_rerun_works_as_updater(self) -> None:
        self._make_github_project()
        self._ok("--set", "mode=pr", "--set", "autonomy-default=queue", "--yes")
        plan = self._plan()
        self.assertEqual(plan["mode"]["status"], "ok")
        self.assertEqual(plan["autonomy-default"]["status"], "difere", "recomendado e pr, escolhido queue")
        self.assertEqual(plan["audit-status"]["status"], "nova", "ainda falta decidir")
        self.assertEqual(plan["skills-audit"]["status"], "padrao")

    def test_detects_heavy_dirs_and_gate_script(self) -> None:
        (self.main / "backend" / ".venv").mkdir(parents=True)
        (self.main / "frontend" / "node_modules").mkdir(parents=True)
        (self.main / "bin").mkdir()
        (self.main / "bin" / "portao.ps1").write_text("exit 0\n", encoding="utf-8")
        plan = self._plan("mode=pr")
        self.assertEqual(plan["worktree-junctions"]["recommended"], ["backend/.venv", "frontend/node_modules"])
        self.assertIn("bin/portao.ps1", plan["gate"]["recommended"][0])

    def test_notes_what_lives_outside_process_json(self) -> None:
        self._make_github_project()
        out = self._ok("--set", "mode=pr").stdout
        self.assertIn("Fora do process.json", out)
        self.assertIn("scaffold protection", out)


if __name__ == "__main__":
    unittest.main()
