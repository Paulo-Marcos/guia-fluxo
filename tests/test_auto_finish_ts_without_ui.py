"""D-191: .ts sem interface (hook, servico) nao conta como mudanca de tela.

Regressao: `uiPaths` trazia `frontend/src/**`, que casava qualquer arquivo do
frontend; um bug em `useCortes.ts` (D-973 no gerador-cortes) ficou `Integrada`
esperando o dono. So arquivo de interface (.tsx/.jsx/.vue/.svelte/.css/.scss/
.html e assets) e tela, e a lista continua configuravel.
"""

from __future__ import annotations

import sys
import unittest

from conftest_paths import CORE_SRC

sys.path.insert(0, str(CORE_SRC))

from _auto_finish import evaluate  # noqa: E402

BASE = {"autonomy": {"default": "pilot", "ceiling": "pilot"}}


def _ui_check(paths: list[str], config: dict | None = None) -> dict:
    task = {"id": "D-001", "kind": "chore", "audit": {"openFindings": {}}}
    checks = evaluate(task, {"humanReason": None}, config or BASE, "pass", paths)
    return next(c for c in checks if c["check"] == "sem mudanca de tela")


class TsWithoutUiTests(unittest.TestCase):
    def test_hooks_and_services_are_not_screen(self) -> None:
        check = _ui_check([
            "frontend/src/features/cortes/useCortes.ts",
            "frontend/src/services/api.ts",
            "frontend/src/lib/formata.js",
        ])
        self.assertTrue(check["ok"], check["evidence"])

    def test_interface_files_and_assets_still_count(self) -> None:
        for path in ("frontend/src/App.tsx", "src/Card.vue", "web/a.scss", "frontend/src/logo.svg",
                     "frontend/src/img/foto.png"):
            with self.subTest(path=path):
                self.assertFalse(_ui_check(["frontend/src/useX.ts", path])["ok"])

    def test_ui_paths_stays_configurable(self) -> None:
        config = {**BASE, "autonomy": {**BASE["autonomy"], "autoFinish": {"uiPaths": ["frontend/src/**"]}}}
        self.assertFalse(_ui_check(["frontend/src/useCortes.ts"], config)["ok"])


if __name__ == "__main__":
    unittest.main()
