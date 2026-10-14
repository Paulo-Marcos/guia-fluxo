"""D-154: o modelo usado (chat e cada subagente) fica na demanda, ao lado do recomendado.

O recomendado vem da triagem (D-153); a auditoria tem piso Opus. Cada registro
diz se o uso ficou acima, igual ou abaixo, e o resumo junta todas as demandas
para o dono ver onde um modelo mais barato bastaria.
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

import _models_used  # noqa: E402


def _task(model: str | None = "sonnet") -> dict:
    return {"id": "D-001", "triage": {"model": model, "audit": "opus"} if model else None}


class RecordTests(unittest.TestCase):
    def test_compares_with_the_triage(self) -> None:
        task = _task("sonnet")
        self.assertEqual(_models_used.record(task, "chat", "opus", "implementar", "high")["vs"], "acima")
        self.assertEqual(_models_used.record(task, "subagent", "haiku", "localizar codigo", None)["vs"], "abaixo")
        self.assertEqual(_models_used.record(task, "subagent", "sonnet", "editar 1 arquivo", None)["vs"], "igual")
        self.assertEqual(len(task["modelsUsed"]), 3)

    def test_audit_has_an_opus_floor(self) -> None:
        entry = _models_used.record(_task("haiku"), "subagent", "opus", "auditar o PR", None)
        self.assertEqual((entry["recommended"], entry["vs"]), ("opus", "igual"))

    def test_without_triage_is_marked(self) -> None:
        self.assertEqual(_models_used.record(_task(None), "chat", "opus", "implementar", None)["vs"], "sem triagem")

    def test_unknown_values_are_refused(self) -> None:
        with self.assertRaises(SystemExit):
            _models_used.record(_task(), "chat", "gpt", "x", None)
        with self.assertRaises(SystemExit):
            _models_used.record(_task(), "robo", "opus", "x", None)

    def test_summary_lists_what_ran_above(self) -> None:
        task = _task("sonnet")
        _models_used.record(task, "chat", "opus", "implementar", None)
        _models_used.record(task, "subagent", "sonnet", "editar", None)
        result = _models_used.summary([task, {"id": "D-002"}])
        self.assertEqual(result["counts"]["acima"], 1)
        self.assertEqual(result["counts"]["igual"], 1)
        self.assertEqual(result["above"][0]["task"], "D-001")


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class ModelCommandTests(unittest.TestCase):
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
        (self.sb / ".guia" / "process.json").write_text(json.dumps({}), encoding="utf-8")
        self._ok("bug", "Corrida no worker")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _ok(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run([sys.executable, "core/src/guia.py", *args], cwd=self.sb,
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def test_records_lists_and_summarizes(self) -> None:
        out = self._ok("model", "D-001", "--who", "subagent", "--model", "opus", "--purpose", "auditar o PR").stdout
        self.assertIn("MODELO USADO D-001: subagent opus (auditar o PR) - recomendado opus: igual", out)
        stored = json.loads(self._ok("model", "D-001", "--json").stdout)["modelsUsed"]
        self.assertEqual([e["model"] for e in stored], ["opus"])
        summary = json.loads(self._ok("model", "--summary", "--json").stdout)
        self.assertEqual(summary["counts"]["igual"], 1)


if __name__ == "__main__":
    unittest.main()
