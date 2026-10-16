"""D-180: demanda que deu ready antes do primeiro PR do projeto e legado.

No gerador-cortes D-898..D-903 e D-911 ficaram em `Aguardando validacao` com o
ready do fluxo antigo (codigo commitado direto na base); o condutor mandava
`ship`, sem branch nem PR para abrir. Agora o `next` para e diz ao dono.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import CORE_LOCK, CORE_SRC

FIRST_PR = "2026-10-13T15:22:29-03:00"


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class LegacyReadyTests(unittest.TestCase):
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
        (self.sb / ".guia" / "process.json").write_text(json.dumps(
            {"delivery": {"mode": "pr"}, "autonomy": {"default": "pilot", "ceiling": "pilot"}}), encoding="utf-8")
        for title in ("Antiga", "Primeira por PR"):
            result = self._run("feature", title)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, "core/src/guia.py", *args], cwd=self.sb,
                              capture_output=True, text=True, encoding="utf-8")

    def _set(self, task_id: str, **fields) -> None:
        path = self.sb / ".guia" / "tasks.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        next(t for t in data["tasks"] if t["id"] == task_id).update(fields)
        path.write_text(json.dumps(data), encoding="utf-8")

    def _next(self, task_id: str) -> dict:
        result = self._run("next", task_id, "--json")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_ready_before_the_first_pr_stops_for_the_owner(self) -> None:
        self._set("D-002", status="Em PR", pr={"number": 1, "head": "a" * 40, "shippedAt": FIRST_PR})
        self._set("D-001", status="Aguardando validacao", readyAt="2026-10-08T12:30:11-03:00")
        step = self._next("D-001")
        self.assertEqual((step["step"], step["owner"]), ("stop", "dono"))
        self.assertIn("legado", step["why"])
        self.assertIn("2026-10-13", step["why"])

    def test_ready_after_the_first_pr_still_ships(self) -> None:
        self._set("D-002", status="Em PR", pr={"number": 1, "head": "a" * 40, "shippedAt": FIRST_PR})
        self._set("D-001", status="Aguardando validacao", readyAt="2026-10-14T09:00:00-03:00")
        self.assertEqual(self._next("D-001")["step"], "ship")

    def test_project_without_any_pr_yet_ships(self) -> None:
        self._set("D-001", status="Aguardando validacao", readyAt="2026-10-08T12:30:11-03:00")
        self.assertEqual(self._next("D-001")["step"], "ship", "sem PR nenhum ainda, nao ha marco")


if __name__ == "__main__":
    unittest.main()
