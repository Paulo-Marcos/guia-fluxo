"""D-179: o auto-finish nao conta arquivo de teste como mudanca de tela.

Regressao: `uiPaths` (`frontend/src/**`, `**/*.tsx`) casava os testes do
frontend, e o check "sem mudanca de tela" reprovava demandas que so tocaram
teste (D-931 no gerador-cortes ficou `Integrada` esperando o dono).
"""

from __future__ import annotations

import sys
import unittest

from conftest_paths import CORE_SRC

sys.path.insert(0, str(CORE_SRC))

from _auto_finish import evaluate  # noqa: E402

CONFIG = {"autonomy": {"default": "pilot", "ceiling": "pilot"}}


def _ui_check(paths: list[str]) -> dict:
    task = {"id": "D-001", "kind": "chore", "audit": {"openFindings": {}}}
    checks = evaluate(task, {"humanReason": None}, CONFIG, "pass", paths)
    return next(c for c in checks if c["check"] == "sem mudanca de tela")


class TestsAreNotUiTests(unittest.TestCase):
    def test_frontend_tests_alone_are_not_a_screen_change(self) -> None:
        check = _ui_check([
            "frontend/src/features/editor/__tests__/numeroNaZona.test.ts",
            "frontend/src/features/shorts/__tests__/secoesDoEstilo.test.tsx",
            "backend/tests/test_x.py",
        ])
        self.assertTrue(check["ok"], check["evidence"])

    def test_a_real_component_still_counts_as_screen(self) -> None:
        check = _ui_check([
            "frontend/src/features/shorts/__tests__/secoesDoEstilo.test.tsx",
            "frontend/src/features/shorts/SecoesDoEstilo.tsx",
        ])
        self.assertFalse(check["ok"])
        self.assertIn("SecoesDoEstilo.tsx", check["evidence"])
        self.assertNotIn("secoesDoEstilo.test.tsx", check["evidence"])


if __name__ == "__main__":
    unittest.main()
