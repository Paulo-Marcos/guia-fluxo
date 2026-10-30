"""D-205: o plano explicado ao dono, em linguagem acessivel, antes do codigo.

`plan/start --brief|--brief-file` grava; `status` e o painel mostram; com
`briefing.required` no process.json, o `next` pede `brief` e o `ready` recusa.
Sem a chave, nada muda (projetos existentes e o fallback do process.json).
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

import _task_view  # noqa: E402

BRIEF = "Duas fichas na demanda.\nA segunda e para o dono."


def _task(**extra) -> dict:
    return {"id": "D-001", "kind": "feature", "title": "Painel", "status": "Em desenvolvimento",
            "executionPlan": ["passo"], **extra}


class BriefingViewTests(unittest.TestCase):
    def test_required_only_when_the_config_says_true(self) -> None:
        self.assertFalse(_task_view.briefing_required({}))
        self.assertFalse(_task_view.briefing_required(None))
        self.assertFalse(_task_view.briefing_required({"briefing": {"required": "sim"}}))
        self.assertTrue(_task_view.briefing_required({"briefing": {"required": True}}))

    def test_missing_only_when_required_and_the_work_is_about_to_happen(self) -> None:
        self.assertTrue(_task_view.missing_briefing(_task(), True))
        self.assertFalse(_task_view.missing_briefing(_task(), False))
        self.assertFalse(_task_view.missing_briefing(_task(briefing={"text": "x"}), True))
        self.assertFalse(_task_view.missing_briefing(_task(briefing={"text": "   "}), False))
        self.assertTrue(_task_view.missing_briefing(_task(briefing={"text": "   "}), True))
        self.assertFalse(_task_view.missing_briefing(_task(status="Backlog"), True))
        self.assertFalse(_task_view.missing_briefing(_task(kind="epic"), True))

    def test_text_shows_the_briefing_keeping_its_lines(self) -> None:
        text = _task_view.format_text(_task(briefing={"text": BRIEF, "at": "2026-10-29T10:00:00"}), "✨", True)
        self.assertIn("Explicacao ao dono:\n  Duas fichas na demanda.\n  A segunda e para o dono.", text)
        self.assertNotIn("Sem explicacao", text)

    def test_text_warns_only_when_required(self) -> None:
        self.assertIn("Sem explicacao ao dono", _task_view.format_text(_task(), "✨", True))
        self.assertIn("plan D-001 --brief-file", _task_view.format_text(_task(), "✨", True))
        self.assertNotIn("Sem explicacao ao dono", _task_view.format_text(_task(), "✨"))

    def test_detail_carries_the_briefing_for_the_dashboard(self) -> None:
        info = _task_view.detail(_task(briefing={"text": BRIEF, "at": "2026-10-29T10:00:00"}), True)
        self.assertEqual(info["briefing"], {"text": BRIEF, "at": "2026-10-29T10:00:00"})
        self.assertFalse(info["missingBriefing"])
        self.assertTrue(_task_view.detail(_task(), True)["missingBriefing"])
        self.assertIsNone(_task_view.detail(_task())["briefing"])


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class BriefingFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.sb = Path(self._tmp.name)
        (self.sb / "core" / "src").mkdir(parents=True)
        (self.sb / "core" / "lock").mkdir(parents=True)
        for src in CORE_SRC.glob("*.py"):
            if not src.name.startswith("__"):
                shutil.copy2(src, self.sb / "core" / "src" / src.name)
        shutil.copy2(CORE_LOCK / "lock_api.py", self.sb / "core" / "lock" / "lock_api.py")
        subprocess.run(["git", "init", "-q"], cwd=self.sb, check=True, capture_output=True)
        (self.sb / ".guia").mkdir()
        self._process(required=True)
        result = self._run("feature", "Mexer")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _process(self, required: bool | None) -> None:
        config: dict = {"delivery": {"mode": "pr"}, "autonomy": {"default": "pilot", "ceiling": "pilot"}}
        if required is not None:
            config["briefing"] = {"required": required}
        (self.sb / ".guia" / "process.json").write_text(json.dumps(config), encoding="utf-8")

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, "core/src/guia.py", *args], cwd=self.sb,
                              capture_output=True, text=True, encoding="utf-8")

    def _next(self) -> dict:
        result = self._run("next", "D-001", "--json")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        return json.loads(result.stdout)

    def _task(self) -> dict:
        return json.loads((self.sb / ".guia" / "tasks.json").read_text(encoding="utf-8"))["tasks"][0]

    def test_required_blocks_next_and_ready_until_recorded(self) -> None:
        step = self._next()
        self.assertEqual((step["step"], step["owner"]), ("brief", "agente"))
        refused = self._run("ready", "D-001", "--file", "x.py")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("ready recusado", refused.stderr)
        self.assertEqual(self._task()["status"], "Em desenvolvimento", "a recusa nao muda a etapa")

        brief = self.sb / "brief.md"
        brief.write_text(BRIEF + "\n", encoding="utf-8")
        recorded = self._run("plan", "D-001", "--brief-file", str(brief))
        self.assertEqual(recorded.returncode, 0, msg=recorded.stdout + recorded.stderr)
        self.assertEqual(self._task()["briefing"]["text"], BRIEF)
        self.assertEqual(self._task()["status"], "Em desenvolvimento", "gravar a explicacao nao muda a etapa")
        self.assertEqual(self._next()["step"], "ready")
        self.assertEqual(self._run("ready", "D-001", "--file", "x.py").returncode, 0)

    def test_status_shows_it_after_start_brief(self) -> None:
        self._run("plan", "D-001")  # volta para Planejada
        started = self._run("start", "D-001", "--step", "a", "--brief", "Vou trocar a ficha.")
        self.assertEqual(started.returncode, 0, msg=started.stdout + started.stderr)
        self.assertNotIn("Sem explicacao", started.stdout)
        status = self._run("status", "D-001").stdout
        self.assertIn("Explicacao ao dono:\n  Vou trocar a ficha.", status)

    def test_start_warns_when_required_and_missing(self) -> None:
        self._run("plan", "D-001")
        self.assertIn("Sem explicacao ao dono", self._run("start", "D-001", "--step", "a").stdout)

    def test_without_the_key_nothing_changes(self) -> None:
        self._process(required=None)
        self.assertEqual(self._next()["step"], "ready")
        self.assertNotIn("Sem explicacao", self._run("status", "D-001").stdout)
        self.assertEqual(self._run("ready", "D-001", "--file", "x.py").returncode, 0)

    def test_brief_and_brief_file_are_exclusive(self) -> None:
        result = self._run("plan", "D-001", "--brief", "a", "--brief-file", "b.md")
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
