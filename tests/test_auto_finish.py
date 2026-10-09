"""D-135: fechar a demanda sem precisar pedir (R7).

No nivel `pilot`, depois do merge o executor fecha a demanda quando todas as
condicoes de `autonomy.autoFinish` valem (tipo, main verde, achados, teste de
regressao no bug, sem tela, fora do alwaysHuman), com `finish.mode = auto` e
a evidencia. Faltou uma, fica `Integrada` com o motivo. Fora do pilot, a
`Integrada` antiga aparece no `status` com "fechar?". GitHub pelo fixture;
o squash e um commit real (o diff da R7 vem do git).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from conftest_paths import CORE_LOCK, CORE_SRC

A = "a" * 40


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=", *args],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8",
    )


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class AutoFinishTests(unittest.TestCase):
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
        self.process = {"delivery": {"mode": "pr"}, "autonomy": {"default": "pilot", "ceiling": "pilot"}}
        self._write_process()
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

    def _write_process(self) -> None:
        (self.main / ".guia" / "process.json").write_text(json.dumps(self.process), encoding="utf-8")

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "core/src/guia.py", *args],
            cwd=self.main, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "GUIA_GH_FIXTURE": str(self.fixture)},
        )

    def _ok(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = self._run(*args)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def _tasks(self) -> list[dict]:
        return json.loads((self.main / ".guia" / "tasks.json").read_text(encoding="utf-8"))["tasks"]

    def _save(self, tasks: list[dict]) -> None:
        path = self.main / ".guia" / "tasks.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["tasks"] = tasks
        path.write_text(json.dumps(data), encoding="utf-8")

    def _integrate(self, kind: str, files: dict[str, str], findings: dict | None = None,
                   main_ci: str = "pass") -> dict:
        """Demanda `kind` com PR auditado; o squash (commit real em main) traz `files`."""
        self._ok(kind, "mexer")
        for rel, content in files.items():
            path = self.main / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        _git(self.main, "add", "-A")
        _git(self.main, "commit", "-q", "-m", "squash")
        _git(self.main, "push", "-q", "origin", "main", "HEAD:refs/heads/b1")
        squash = _git(self.main, "rev-parse", "HEAD").stdout.strip()
        tasks = self._tasks()
        task = tasks[-1]
        task["status"] = "Em PR"
        task["pr"] = {"number": 1, "url": "u", "branch": "b1", "head": A}
        task["audit"] = {"result": "approved", "auditedSha": A, "auditedPatchId": "p"}
        if findings is not None:
            task["audit"]["openFindings"] = findings
        self._save(tasks)
        (self.main / ".guia" / "queue").mkdir(exist_ok=True)
        (self.main / ".guia" / "queue" / f"{task['id']}.msg").write_text("x: t\n\ncorpo\n", encoding="utf-8")
        prs = [{"number": 1, "head": A, "state": "OPEN", "mergeState": "CLEAN", "checks": "pass",
                "patchIds": {A: "p"}, "mainCi": main_ci, "squashSha": squash}]
        Path(str(self.fixture) + ".prs.json").write_text(json.dumps(prs), encoding="utf-8")
        self._ok("queue", "add", task["id"])
        self._ok("approve", task["id"])
        self.out = self._ok("queue", "run").stdout
        return next(t for t in self._tasks() if t["id"] == task["id"])

    def test_pilot_closes_a_safe_chore_with_the_evidence(self) -> None:
        task = self._integrate("chore", {"app.txt": "limpo\n"}, {"BLOQUEANTE": 0, "CORRIGIR": 0})
        self.assertEqual(task["status"], "Validada", self.out)
        self.assertEqual(task["finish"]["mode"], "auto")
        self.assertTrue(all(c["ok"] for c in task["finish"]["checks"]))
        self.assertIn("fechada pelo pilot", self.out)

    def test_feature_stays_integrated_with_the_reason(self) -> None:
        task = self._integrate("feature", {"app.txt": "novo\n"}, {"BLOQUEANTE": 0, "CORRIGIR": 0})
        self.assertEqual(task["status"], "Integrada")
        self.assertIn("pilot nao fechou - tipo permitido", self.out)

    def test_bug_needs_the_regression_test_in_the_squash(self) -> None:
        task = self._integrate("bug", {"app.txt": "fix\n"}, {"BLOQUEANTE": 0, "CORRIGIR": 0})
        self.assertEqual(task["status"], "Integrada")
        self.assertIn("teste de regressao", self.out)
        task = self._integrate("bug", {"app.txt": "fix2\n", "tests/test_app.py": "x = 1\n"},
                               {"BLOQUEANTE": 0, "CORRIGIR": 0})
        self.assertEqual(task["status"], "Validada", self.out)

    def test_ui_change_red_main_or_open_findings_keep_it_for_the_owner(self) -> None:
        zero = {"BLOQUEANTE": 0, "CORRIGIR": 0}
        self.assertEqual(self._integrate("chore", {"frontend/src/a.tsx": "x\n"}, zero)["status"], "Integrada")
        self.assertIn("sem mudanca de tela", self.out)
        self.assertEqual(self._integrate("chore", {"app.txt": "1\n"}, {"CORRIGIR": 1})["status"], "Integrada")
        self.assertIn("achados da auditoria", self.out)
        self.assertEqual(self._integrate("chore", {"app.txt": "2\n"}, None)["status"], "Integrada")
        self.assertIn("audit --finding", self.out)
        self.assertEqual(self._integrate("chore", {"app.txt": "3\n"}, zero, main_ci="pending")["status"], "Integrada")
        self.assertIn("main verde", self.out)

    def test_below_pilot_nothing_closes(self) -> None:
        self.process["autonomy"]["default"] = "queue"
        self._write_process()
        task = self._integrate("chore", {"app.txt": "q\n"}, {"BLOQUEANTE": 0, "CORRIGIR": 0})
        self.assertEqual(task["status"], "Integrada")
        self.assertNotIn("pilot", self.out)

    def test_old_integrated_demand_asks_to_close_in_status(self) -> None:
        self._ok("chore", "velha")
        self._ok("chore", "recente")
        tasks = self._tasks()
        now = datetime.now(timezone.utc)
        for task, days in zip(tasks, (10, 1)):
            task["status"] = "Integrada"
            task["pr"] = {"number": 1, "mergedAt": (now - timedelta(days=days)).isoformat()}
        self._save(tasks)
        out = self._ok("status", "--all").stdout
        self.assertIn(f"Integrada ha 10 dias: {tasks[0]['id']}", out)
        self.assertIn("fechar?", out)
        self.assertNotIn(f"{tasks[1]['id']} recente - fechar?", out)

    def test_audit_records_open_findings(self) -> None:
        probe = (
            "import sys; sys.path.insert(0, 'core/src'); from _cli_audit import _parse_findings as p\n"
            "print(p(['bloqueante=0', 'CORRIGIR=2']))\n"
            "try:\n    p(['CORRIGIR'])\nexcept SystemExit:\n    print('recusado')\n"
        )
        out = subprocess.run([sys.executable, "-c", probe], cwd=self.main, capture_output=True,
                             text=True, encoding="utf-8").stdout
        self.assertIn("{'BLOQUEANTE': 0, 'CORRIGIR': 2}", out)
        self.assertIn("recusado", out)


if __name__ == "__main__":
    unittest.main()
