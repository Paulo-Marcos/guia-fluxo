"""D-195: o painel mostra qual motor os botoes do dono vao rodar.

O retrato de cada projeto traz o caminho do motor (`engine.path`) e se ele
vem da pasta do proprio projeto (`engine.own`); o confirm() dos botoes Retomar
fila e Iniciar executor repete esse caminho e destaca o motor do projeto.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from conftest_paths import ensure_core_importable

ensure_core_importable()

import _dashboard  # noqa: E402
import _dashboard_actions  # noqa: E402
from _dashboard_page import PAGE_HTML  # noqa: E402
from test_dashboard_scroll import DOM_STUB  # noqa: E402


def _project(root: Path) -> Path:
    (root / ".guia").mkdir(parents=True)
    (root / ".guia" / "tasks.json").write_text(json.dumps({"tasks": []}), encoding="utf-8")
    return root


class SnapshotEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)

    def test_project_without_engine_uses_the_panel_engine(self) -> None:
        engine = _dashboard.snapshot(_project(self.tmp / "app"))["engine"]
        self.assertEqual(engine, {"path": str(_dashboard.ENGINE), "own": False})

    def test_project_engine_is_shown_and_flagged_as_own(self) -> None:
        root = _project(self.tmp / "clone")
        script = root / "plugins" / "guia" / "bin" / "guia.py"
        script.parent.mkdir(parents=True)
        script.write_text("print('do projeto')\n", encoding="utf-8")
        engine = _dashboard.snapshot(root)["engine"]
        self.assertEqual(engine, {"path": str(script), "own": True})

    def test_buttons_and_snapshot_agree_on_the_engine(self) -> None:
        root = _project(self.tmp / "dogfood")
        script = root / "core" / "src" / "guia.py"
        script.parent.mkdir(parents=True)
        script.write_text("", encoding="utf-8")
        self.assertEqual(_dashboard_actions.engine_for(root), script)
        self.assertEqual(_dashboard.snapshot(root)["engine"]["path"], str(script))


CONFIRM_PROBE = r"""
(async () => {
  const asked = [];
  window.confirm = q => { asked.push(q); return false; };
  snapshot = SNAPSHOT;
  await refresh();
  select("C:\p");
  document.querySelector(".act .btn").click();
  console.log(JSON.stringify(asked));
})();
"""


def _snapshot(queue: dict, engine: dict) -> dict:
    stages = [{"label": f"Etapa {i}", "cards": []} for i in range(8)]
    base = {"items": [], "history": [], "executor": None, "head": None}
    return {"guia": {"version": "9.9.9", "engine": "x"}, "projects": [{
        "name": "p", "path": "C:\\p", "mode": "pr", "active": 0, "current": None, "stages": stages,
        "doneTotal": 0, "recentDone": [], "queue": dict(base, **queue), "engine": engine,
    }]}


@unittest.skipUnless(shutil.which("node"), "node ausente")
class ConfirmShowsEngineTests(unittest.TestCase):
    def ask(self, snapshot: dict) -> str:
        script = re.search(r"<script>(.*?)</script>", PAGE_HTML, re.S).group(1)
        source = DOM_STUB + script + CONFIRM_PROBE.replace("SNAPSHOT", json.dumps(snapshot))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "probe.js"
            path.write_text(source, encoding="utf-8")
            out = subprocess.run(["node", str(path)], capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(out.returncode, 0, out.stderr)
        asked = json.loads(out.stdout.strip().splitlines()[-1])
        self.assertEqual(len(asked), 1)
        return asked[0]

    def test_resume_highlights_the_project_engine(self) -> None:
        engine = {"path": "C:\\clone\\plugins\\guia\\bin\\guia.py", "own": True}
        question = self.ask(_snapshot({"paused": True}, engine))
        self.assertIn("Retomar a fila", question)
        self.assertIn(engine["path"], question)
        self.assertIn("PRÓPRIO PROJETO", question)

    def test_executor_names_the_panel_engine(self) -> None:
        engine = {"path": "C:\\cache\\guia\\bin\\guia.py", "own": False}
        question = self.ask(_snapshot({}, engine))
        self.assertIn("Iniciar o executor", question)
        self.assertIn("Motor: " + engine["path"] + " (o do painel)", question)
        self.assertNotIn("PRÓPRIO PROJETO", question)


if __name__ == "__main__":
    unittest.main()
