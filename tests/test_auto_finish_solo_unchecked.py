"""D-200: no solo, o aviso de alwaysHuman so vale com o squash conferido.

Squash que o git nao conferiu continua travando o auto-finish mesmo no solo
(ADR-0021) - inclusive com `blockIfUiChanged` desligado, quando a checagem de
tela nao cobre mais esse caso.
"""

from __future__ import annotations

import sys
import unittest

from conftest_paths import CORE_SRC

sys.path.insert(0, str(CORE_SRC))

from _auto_finish import evaluate  # noqa: E402


class UncheckedSquashTests(unittest.TestCase):
    def test_solo_always_human_holds_when_the_squash_was_not_checked(self) -> None:
        config = {"delivery": {"mode": "pr"}, "autonomy": {
            "default": "pilot", "ceiling": "pilot", "solo": "on", "autoFinish": {"blockIfUiChanged": False}}}
        task = {"kind": "chore", "audit": {"result": "approved"}}
        checks = {c["check"]: c for c in evaluate(task, {"humanReason": "toca caminho alwaysHuman: x"}, config, "pass", None)}
        self.assertFalse(checks["fora do alwaysHuman"]["ok"])


if __name__ == "__main__":
    unittest.main()
