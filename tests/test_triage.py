"""D-153: a triagem de complexidade recomenda modelo e esforco por uma regua fixa.

Trivial -> haiku/low; normal -> sonnet/medium; complexa (3+ areas, risco ou
incerteza) -> opus/high; extrema -> opus/max com o Fable so como sugestao (com
pergunta, por padrao). A auditoria nunca fica abaixo de opus. O comando grava a
recomendacao na demanda, com o porque.
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

import _triage  # noqa: E402


def _rec(kind: str, scope: int = 1, risks=(), uncertain=False, irreversible=False, config=None) -> dict:
    return _triage.recommend({"kind": kind}, config or {}, scope, list(risks), uncertain, irreversible)


class RulerTests(unittest.TestCase):
    def test_trivial_goes_to_haiku(self) -> None:
        rec = _rec("chore")
        self.assertEqual((rec["tier"], rec["model"], rec["effort"]), ("trivial", "haiku", "low"))

    def test_normal_goes_to_sonnet(self) -> None:
        rec = _rec("feature", scope=2)
        self.assertEqual((rec["tier"], rec["model"], rec["effort"]), ("normal", "sonnet", "medium"))

    def test_scope_risk_or_uncertainty_make_it_complex(self) -> None:
        for rec in (_rec("feature", scope=3), _rec("bug", risks=["auth"]), _rec("bug", uncertain=True)):
            self.assertEqual((rec["tier"], rec["model"], rec["effort"]), ("complexa", "opus", "high"))

    def test_extreme_suggests_fable_but_keeps_opus(self) -> None:
        rec = _rec("feature", risks=["migration", "data"], uncertain=True)
        self.assertEqual((rec["tier"], rec["model"], rec["effort"]), ("extrema", "opus", "max"))
        self.assertEqual(rec["suggestion"]["model"], "fable")
        self.assertTrue(rec["suggestion"]["ask"], "o padrao e perguntar antes")
        never = _rec("feature", risks=["prod"], irreversible=True, config={"models": {"fable": "never"}})
        self.assertIsNone(never["suggestion"])

    def test_audit_never_below_opus(self) -> None:
        self.assertEqual(_rec("chore")["audit"], "opus")

    def test_tiers_are_configurable(self) -> None:
        rec = _rec("feature", scope=2, config={"models": {"tiers": {"normal": "opus"}}})
        self.assertEqual(rec["model"], "opus")

    def test_unknown_risk_is_refused(self) -> None:
        with self.assertRaises(SystemExit):
            _rec("bug", risks=["clima"])


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class TriageCommandTests(unittest.TestCase):
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

    def test_records_and_shows_the_recommendation(self) -> None:
        out = self._ok("triage", "D-001", "--scope", "2", "--risk", "concurrency", "--uncertain").stdout
        self.assertIn("MODELO RECOMENDADO D-001: complexa: Opus 5.5, esforco high", out)
        self.assertIn("risco: concurrency", out)
        stored = json.loads(self._ok("triage", "D-001", "--json").stdout)["triage"]
        self.assertEqual(stored["signals"], {"scope": 2, "risks": ["concurrency"], "uncertain": True, "irreversible": False})


if __name__ == "__main__":
    unittest.main()
