"""D-192: detalhe da demanda - `status` legivel, `--json`, plano e painel."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import REPO_ROOT, ensure_core_importable

ensure_core_importable()

import _dashboard  # noqa: E402
import _task_view  # noqa: E402

CORE_SRC = REPO_ROOT / "core" / "src"
CORE_LOCK = REPO_ROOT / "core" / "lock"


def _seed(sandbox: Path) -> None:
    (sandbox / "core" / "src").mkdir(parents=True)
    (sandbox / "core" / "lock").mkdir(parents=True)
    for src in CORE_SRC.glob("*.py"):
        shutil.copy2(src, sandbox / "core" / "src" / src.name)
    shutil.copy2(CORE_LOCK / "lock_api.py", sandbox / "core" / "lock" / "lock_api.py")


def _task(**extra) -> dict:
    return {"id": "D-001", "kind": "feature", "title": "Painel", "status": "Em desenvolvimento",
            "context": "Por que existe", "createdAt": "2026-10-01", **extra}


class TaskViewTests(unittest.TestCase):
    def test_missing_plan_only_where_the_work_is_about_to_happen(self) -> None:
        self.assertTrue(_task_view.missing_plan(_task()))
        self.assertTrue(_task_view.missing_plan(_task(status="Planejada", executionPlan=None)))
        self.assertFalse(_task_view.missing_plan(_task(executionPlan=["passo"])))
        self.assertFalse(_task_view.missing_plan(_task(status="Backlog")))
        self.assertFalse(_task_view.missing_plan(_task(status="Validada")))
        self.assertFalse(_task_view.missing_plan(_task(kind="epic")))

    def test_timeline_rebuilds_the_steps_in_order(self) -> None:
        task = _task(startedAt="2026-10-02T10:00:00", readyAt="2026-10-03T09:00:00",
                     pr={"number": 7, "shippedAt": "2026-10-03T11:00:00"},
                     audit={"result": "approved", "at": "2026-10-03T12:00:00"},
                     blocks=[{"reason": "API", "at": "2026-10-02", "unblockedAt": "2026-10-02"}])
        steps = [s["step"] for s in _task_view.timeline(task)]
        self.assertEqual(steps, ["Criada", "Em desenvolvimento", "Bloqueada: API", "Desbloqueada",
                                 "Aguardando validacao", "PR #7", "Auditoria: approved"])

    def test_detail_carries_what_the_owner_reads(self) -> None:
        info = _task_view.detail(_task(executionPlan=["a", "b"], modifiedFiles=["x.py"], validations=["ok"],
                                       pending=["testar"], chat={"title": "D-001 chat", "session": "local_1"},
                                       requestToTest=[{"request": "abre", "test": "t::abre"}]))
        self.assertEqual(info["plan"], ["a", "b"])
        self.assertFalse(info["missingPlan"])
        self.assertEqual(info["files"], ["x.py"])
        self.assertEqual(info["chat"], {"title": "D-001 chat", "session": "local_1"})
        self.assertEqual(info["requests"], [{"request": "abre", "test": "t::abre"}])

    def test_text_names_the_sections_and_warns_without_plan(self) -> None:
        text = _task_view.format_text(_task(pending=["testar"]), "✨")
        self.assertTrue(text.startswith("D-001 ✨ Painel"))
        self.assertIn("Contexto:\n  Por que existe", text)
        self.assertIn("Sem plano registrado", text)
        self.assertIn("plan D-001 --step", text)
        self.assertIn("Pendencias:\n  - testar", text)
        self.assertIn("status D-001 --json", text)


class DashboardDetailTests(unittest.TestCase):
    def test_card_carries_the_detail(self) -> None:
        root = Path(tempfile.mkdtemp()) / "app"
        (root / ".guia").mkdir(parents=True)
        (root / ".guia" / "tasks.json").write_text(json.dumps({"tasks": [_task()]}), encoding="utf-8")
        card = _dashboard.snapshot(root)["stages"][2]["cards"][0]
        self.assertEqual(card["id"], "D-001")
        self.assertTrue(card["detail"]["missingPlan"])
        self.assertEqual(card["detail"]["context"], "Por que existe")

    def test_engine_version_from_repo_and_from_plugin(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        repo_src = tmp / "repo" / "core" / "src"
        repo_src.mkdir(parents=True)
        (tmp / "repo" / "VERSION").write_text("1.2.3\n", encoding="utf-8")
        self.assertEqual(_dashboard.engine_version(repo_src)["version"], "1.2.3")
        plugin_bin = tmp / "plugin" / "bin"
        plugin_bin.mkdir(parents=True)
        (tmp / "plugin" / ".claude-plugin").mkdir()
        (tmp / "plugin" / ".claude-plugin" / "plugin.json").write_text('{"version": "4.5.6"}', encoding="utf-8")
        self.assertEqual(_dashboard.engine_version(plugin_bin)["version"], "4.5.6")
        self.assertIsNone(_dashboard.engine_version(tmp / "nada")["version"])

    def test_overview_reports_the_running_version(self) -> None:
        version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(_dashboard.overview([])["guia"]["version"], version)


class StatusCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sandbox = Path(tempfile.mkdtemp())
        _seed(self.sandbox)
        self._run("init", "--project-name", "t", "--no-locks")
        self._run("feature", "Primeira", "--context", "Motivo da primeira")

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run([sys.executable, "core/src/guia.py", *args], cwd=self.sandbox,
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_status_is_readable_and_json_keeps_the_old_contract(self) -> None:
        text = self._run("status", "D-001").stdout
        self.assertIn("Contexto:\n  Motivo da primeira", text)
        self.assertIn("Sem plano registrado", text)
        self.assertFalse(text.lstrip().startswith("{"))
        raw = self._run("status", "D-001", "--json").stdout
        data, end = json.JSONDecoder().raw_decode(raw)
        self.assertEqual(data["id"], "D-001")
        self.assertIn("NOME DA DEMANDA:", raw[end:])

    def test_plan_step_records_without_moving_the_stage(self) -> None:
        self._run("plan", "D-001", "--step", "fazer A", "--step", "fazer B")
        data, _ = json.JSONDecoder().raw_decode(self._run("status", "D-001", "--json").stdout)
        self.assertEqual(data["status"], "Em desenvolvimento")
        self.assertEqual(data["executionPlan"], ["fazer A", "fazer B"])
        self.assertIn("Plano:\n  1. fazer A\n  2. fazer B", self._run("status", "D-001").stdout)
        self.assertNotIn("Sem plano registrado", self._run("status", "D-001").stdout)

    def test_start_records_steps_or_warns(self) -> None:
        self._run("feature", "Segunda", "--status", "planned")
        out = self._run("start", "D-002").stdout
        self.assertIn("Sem plano registrado", out)
        self._run("feature", "Terceira", "--status", "planned")
        out = self._run("start", "D-003", "--step", "passo unico").stdout
        self.assertNotIn("Sem plano registrado", out)


if __name__ == "__main__":
    unittest.main()
