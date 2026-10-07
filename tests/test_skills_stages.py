"""D-114: skills configuraveis por etapa (R12) nas etapas que ja existem.

`skills.<etapa>` no process.json: ausente = padrao do plugin; nome ou lista =
essas skills; null = etapa sem skill. O motor anuncia a skill da etapa (quem
confere se existe e roda e o agente) e registra o que aconteceu em
`skillsRun` (`ran`, `missing`, `disabled`). Sem `skills`, as sugestoes sao as
de hoje.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import CORE_LOCK, CORE_SRC, ensure_core_importable

ensure_core_importable()

import _constants  # noqa: E402
import _skills  # noqa: E402


class StageResolutionTests(unittest.TestCase):
    def test_absent_uses_plugin_defaults(self) -> None:
        self.assertEqual(_skills.stage_skills("ready", {}), (["delivery-report"], False))
        self.assertEqual(
            _skills.stage_skills("quality", {}),
            (list(_constants.QUALITY_SKILL_SUGGESTIONS), False),
        )

    def test_name_list_and_null(self) -> None:
        self.assertEqual(_skills.stage_skills("ready", {"skills": {"ready": "relatorio"}}), (["relatorio"], False))
        self.assertEqual(
            _skills.stage_skills("quality", {"skills": {"quality": ["a", "b"]}}), (["a", "b"], False)
        )
        self.assertEqual(_skills.stage_skills("ready", {"skills": {"ready": None}}), ([], True))


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class StageCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.sb = Path(self._tmp.name)
        (self.sb / "core" / "src").mkdir(parents=True)
        (self.sb / "core" / "lock").mkdir(parents=True)
        for src in CORE_SRC.glob("*.py"):
            if not src.name.startswith("__"):
                shutil.copy2(src, self.sb / "core" / "src" / src.name)
        shutil.copy2(CORE_LOCK / "lock_api.py", self.sb / "core" / "lock" / "lock_api.py")
        for args in (("init", "-q"), ("config", "user.email", "t@t"), ("config", "user.name", "t")):
            subprocess.run(["git", *args], cwd=self.sb, check=True, capture_output=True)
        self._ok("chore", "mexer em a")
        (self.sb / "a.txt").write_text("a\n", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _skills_config(self, skills: dict) -> None:
        path = self.sb / ".guia" / "process.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["skills"] = skills
        path.write_text(json.dumps(data), encoding="utf-8")

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "core/src/guia.py", *args],
            cwd=self.sb, capture_output=True, text=True, encoding="utf-8",
        )

    def _ok(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = self._run(*args)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def _skills_run(self) -> list[dict]:
        tasks = json.loads((self.sb / ".guia" / "tasks.json").read_text(encoding="utf-8"))
        return tasks["tasks"][0].get("skillsRun", [])

    def test_ready_announces_the_default_skill(self) -> None:
        result = self._ok("ready", "D-001", "--file", "a.txt")
        self.assertIn("etapa ready", result.stderr)
        self.assertIn("delivery-report", result.stderr)

    def test_ready_records_ran_and_missing(self) -> None:
        self._ok("ready", "D-001", "--file", "a.txt", "--skill-ran", "delivery-report", "--skill-missing", "outra")
        runs = [(r["stage"], r["skill"], r["result"]) for r in self._skills_run()]
        self.assertEqual(runs, [("ready", "delivery-report", "ran"), ("ready", "outra", "missing")])

    def test_null_disables_the_stage(self) -> None:
        self._skills_config({"ready": None})
        result = self._ok("ready", "D-001", "--file", "a.txt")
        self.assertIn("desligada", result.stderr)
        self.assertNotIn("delivery-report", result.stderr)
        self.assertEqual([(r["stage"], r["result"]) for r in self._skills_run()], [("ready", "disabled")])

    def test_quality_override_replaces_the_suggestions(self) -> None:
        self._skills_config({"quality": ["minha-review"]})
        result = self._run("finish", "D-001", "--file", "a.txt", "--no-commit")
        self.assertNotEqual(result.returncode, 0, "o gate do D-095 continua exigindo a confirmacao")
        self.assertIn("minha-review", result.stdout)
        self.assertNotIn("clean-code-review", result.stdout)

    def test_quality_skill_counts_as_ran(self) -> None:
        self._ok(
            "finish", "D-001", "--file", "a.txt", "--no-commit",
            "--quality-checked", "--quality-skill", "clean-code-review",
        )
        runs = [(r["stage"], r["skill"], r["result"]) for r in self._skills_run()]
        self.assertIn(("quality", "clean-code-review", "ran"), runs)


if __name__ == "__main__":
    unittest.main()
