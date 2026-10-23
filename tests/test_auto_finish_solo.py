"""D-200: finish 100% automatico no pilot SOLO.

No solo (ADR-0021), tela e caminho alwaysHuman deixam de segurar o
auto-finish: viram aviso registrado na demanda (o dono revisa depois). Bug
sem teste de regressao continua travando - quem corrige e o agente, antes do
ship. E a demanda que ja estava `Integrada` quando o solo foi ligado fecha
na proxima passada do executor (varredura), com o mesmo checklist. Fora do
solo nada muda.
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

sys.path.insert(0, str(CORE_SRC))

from _auto_finish import evaluate  # noqa: E402

PILOT = {"default": "pilot", "ceiling": "pilot"}
APPROVED = {"result": "approved"}
UI = ["frontend/src/a.tsx", "core/x.py"]


def _config(**autonomy: object) -> dict:
    return {"delivery": {"mode": "pr"}, "autonomy": {**PILOT, **autonomy}}


def _checks(task: dict, config: dict, paths: list[str], reason: str | None = None) -> dict[str, dict]:
    return {c["check"]: c for c in evaluate(task, {"humanReason": reason}, config, "pass", paths)}


class SoloWarningsTests(unittest.TestCase):
    def test_solo_ui_change_is_a_recorded_warning(self) -> None:
        checks = _checks({"kind": "chore", "audit": APPROVED}, _config(solo="on"), UI)
        ui = checks["sem mudanca de tela"]
        self.assertTrue(ui["ok"], ui)
        self.assertTrue(ui.get("warning"), ui)
        self.assertIn("frontend/src/a.tsx", ui["evidence"])

    def test_solo_always_human_is_a_recorded_warning(self) -> None:
        reason = "toca caminho alwaysHuman: .github/workflows/ci.yml"
        checks = _checks({"kind": "feature", "audit": APPROVED}, _config(solo="on"), ["core/x.py"], reason)
        human = checks["fora do alwaysHuman"]
        self.assertTrue(human["ok"], human)
        self.assertTrue(human.get("warning"), human)
        self.assertIn(".github/workflows/ci.yml", human["evidence"])
        self.assertTrue(all(c["ok"] for c in checks.values()), checks)

    def test_solo_bug_without_regression_test_still_holds(self) -> None:
        checks = _checks({"kind": "bug", "audit": APPROVED}, _config(solo="on"), ["core/x.py"])
        self.assertFalse(checks["teste de regressao"]["ok"])

    def test_solo_unchecked_paths_still_hold(self) -> None:
        checks = {c["check"]: c for c in evaluate({"kind": "chore", "audit": APPROVED}, {}, _config(solo="on"), "pass", None)}
        self.assertFalse(checks["sem mudanca de tela"]["ok"])

    def test_without_solo_ui_and_always_human_still_hold(self) -> None:
        zero = {"result": "approved", "openFindings": {"BLOQUEANTE": 0, "CORRIGIR": 0}}
        checks = _checks({"kind": "chore", "audit": zero}, _config(), UI, "desbloqueia trava: x")
        self.assertFalse(checks["sem mudanca de tela"]["ok"])
        self.assertFalse(checks["fora do alwaysHuman"]["ok"])
        self.assertFalse(any(c.get("warning") for c in checks.values()))


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=", *args],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8",
    )


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class SweepTests(unittest.TestCase):
    """A varredura: `Integrada` antiga fecha na passada do executor (so no solo)."""

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
        (self.main / ".gitignore").write_text(".guia/\ncore/\n", encoding="utf-8")
        (self.main / "app.txt").write_text("app\n", encoding="utf-8")
        remote = base / "remote.git"
        _git(base, "init", "-q", "--bare", str(remote))
        for args in (("init", "-q", "-b", "main"), ("add", "."), ("commit", "-q", "-m", "init"),
                     ("remote", "add", "origin", str(remote)), ("push", "-q", "-u", "origin", "main")):
            self.assertEqual(_git(self.main, *args).returncode, 0, msg=str(args))
        self.fixture = base / "gh.json"
        self.fixture.write_text(json.dumps({"__auth__": True}), encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, "core/src/guia.py", *args],
            cwd=self.main, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "GUIA_GH_FIXTURE": str(self.fixture)},
        )
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def _tasks(self) -> list[dict]:
        return json.loads((self.main / ".guia" / "tasks.json").read_text(encoding="utf-8"))["tasks"]

    def _integrated(self, kind: str, files: dict[str, str], main_ci: str = "pass", **autonomy: object) -> str:
        """Demanda ja `Integrada` (merge antes do solo), squash real com `files`."""
        (self.main / ".guia" / "process.json").write_text(json.dumps(_config(**autonomy)), encoding="utf-8")
        self._run(kind, "antiga")
        for rel, content in files.items():
            path = self.main / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        _git(self.main, "add", "-A")
        _git(self.main, "commit", "-q", "-m", "squash")
        squash = _git(self.main, "rev-parse", "HEAD").stdout.strip()
        path = self.main / ".guia" / "tasks.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        task = data["tasks"][-1]
        task["status"] = "Integrada"
        task["pr"] = {"number": 7, "url": "u", "mergedAt": "2026-10-20T00:00:00Z"}
        task["audit"] = APPROVED
        path.write_text(json.dumps(data), encoding="utf-8")
        prs = [{"number": 7, "state": "MERGED", "mergeCommit": squash, "mainCi": main_ci}]
        Path(str(self.fixture) + ".prs.json").write_text(json.dumps(prs), encoding="utf-8")
        return task["id"]

    def _task(self, task_id: str) -> dict:
        return next(t for t in self._tasks() if t["id"] == task_id)

    def test_solo_sweep_closes_an_old_integrated_feature_with_ui_as_warning(self) -> None:
        task_id = self._integrated("feature", {"frontend/src/a.tsx": "x\n"}, solo="on")
        out = self._run("queue", "run").stdout
        task = self._task(task_id)
        self.assertEqual(task["status"], "Validada", out)
        self.assertEqual(task["finish"]["mode"], "auto")
        self.assertIn("varredura", out)
        self.assertEqual([w["check"] for w in task["finish"]["warnings"]], ["sem mudanca de tela"])
        self.assertTrue(any("aviso" in line and "frontend/src/a.tsx" in line for line in task["summary"]), task["summary"])

    def test_solo_sweep_keeps_a_bug_without_regression_test(self) -> None:
        task_id = self._integrated("bug", {"app.txt": "fix\n"}, solo="on")
        out = self._run("queue", "run").stdout
        task = self._task(task_id)
        self.assertEqual(task["status"], "Integrada", out)
        self.assertIn("teste de regressao", out)
        failed = [c["check"] for c in task["autoFinish"]["checks"] if not c["ok"]]
        self.assertEqual(failed, ["teste de regressao"])

    def test_solo_sweep_waits_for_a_green_main(self) -> None:
        task_id = self._integrated("chore", {"app.txt": "x\n"}, main_ci="pending", solo="on")
        self._run("queue", "run")
        self.assertEqual(self._task(task_id)["status"], "Integrada")

    def test_without_solo_the_sweep_does_not_run(self) -> None:
        task_id = self._integrated("chore", {"app.txt": "x\n"})
        out = self._run("queue", "run").stdout
        task = self._task(task_id)
        self.assertEqual(task["status"], "Integrada", out)
        self.assertNotIn("autoFinish", task)
        self.assertNotIn("varredura", out)


if __name__ == "__main__":
    unittest.main()
