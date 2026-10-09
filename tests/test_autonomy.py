"""D-133: niveis de autonomia por demanda (R6).

`manual` < `pr` < `queue` < `pilot`. O nivel mora na demanda (o chat pode
cair e voltar); sem nivel, vale `autonomy.default` (sem config, `manual`:
nada muda). O teto `autonomy.ceiling` e do projeto. Subir e so do usuario,
descer qualquer um. O nivel aparece no nome da demanda.
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


class AutonomyTests(unittest.TestCase):
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
        self._ok("chore", "arrumar")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _process(self, data: dict) -> None:
        path = self.sb / ".guia" / "process.json"
        current = json.loads(path.read_text(encoding="utf-8"))
        current.update(data)
        path.write_text(json.dumps(current), encoding="utf-8")

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "core/src/guia.py", *args],
            cwd=self.sb, capture_output=True, text=True, encoding="utf-8",
        )

    def _ok(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = self._run(*args)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def _task(self) -> dict:
        return json.loads((self.sb / ".guia" / "tasks.json").read_text(encoding="utf-8"))["tasks"][0]

    def test_without_config_the_level_is_manual_and_the_title_is_unchanged(self) -> None:
        shown = json.loads(self._ok("autonomy", "D-001", "--json").stdout)
        self.assertEqual((shown["effective"], shown["default"]), ("manual", "manual"))
        title = (self.sb / ".guia" / "demand-title.txt").read_text(encoding="utf-8").strip()
        self.assertNotIn("·", title)

    def test_user_sets_the_level_on_the_demand_and_it_shows_in_the_title(self) -> None:
        out = self._ok("autonomy", "queue", "D-001").stdout
        level = self._task()["autonomy"]
        self.assertEqual((level["level"], level["setBy"]), ("queue", "user"))
        self.assertIn("#DEV·queue", out)
        self.assertIn("#DEV·queue", (self.sb / ".guia" / "demand-title.txt").read_text(encoding="utf-8"))

    def test_ceiling_refuses_and_caps_the_default(self) -> None:
        self._process({"autonomy": {"default": "queue", "ceiling": "pr"}})
        result = self._run("autonomy", "queue", "D-001")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("teto", result.stdout + result.stderr)
        shown = json.loads(self._ok("autonomy", "D-001", "--json").stdout)
        self.assertEqual(shown["effective"], "pr", "o default acima do teto e limitado pelo teto")

    def test_agent_can_lower_but_never_raise(self) -> None:
        self._ok("autonomy", "queue", "D-001")
        refused = self._run("autonomy", "pilot", "D-001", "--by", "agent")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("usuario", refused.stdout + refused.stderr)
        self._ok("autonomy", "pr", "D-001", "--by", "agent")
        self.assertEqual((self._task()["autonomy"]["level"], self._task()["autonomy"]["setBy"]), ("pr", "agent"))

    def test_invalid_level_is_refused(self) -> None:
        self.assertNotEqual(self._run("autonomy", "total", "D-001").returncode, 0)


if __name__ == "__main__":
    unittest.main()
