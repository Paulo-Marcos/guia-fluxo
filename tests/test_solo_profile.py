"""D-193 (ADR-0021): perfil SOLO local - o pilot que nao para no dono.

Projeto solo e local (so o dono usa e reverte se der errado): com
`autonomy.solo`, o [unlock:] fica so como rastro e nao segura a fila, os
caminhos sensiveis so param se o dono listar, a auditoria aprovada prova os
achados (o agente corrige antes do approve) e a feature fecha sozinha. Sem o
solo, nada muda - exceto que `alwaysHuman: []` explicito agora desliga.
"""

from __future__ import annotations

import sys
import unittest

from conftest_paths import CORE_SRC

sys.path.insert(0, str(CORE_SRC))

from _auto_finish import evaluate, settings  # noqa: E402
from _autonomy import human_reasons  # noqa: E402
from _configure import STEPS_BY_ID, Context  # noqa: E402

PILOT = {"default": "pilot", "ceiling": "pilot"}
UNLOCK = "feat: x\n\n[unlock:testes-sao-contrato] motivo: ajuste do teste\n"


def _config(**autonomy: object) -> dict:
    return {"delivery": {"mode": "pr"}, "autonomy": {**PILOT, **autonomy}}


def _checks(task: dict, config: dict) -> dict[str, dict]:
    return {c["check"]: c for c in evaluate(task, {"humanReason": None}, config, "pass", ["core/x.py"])}


class HumanReasonsTests(unittest.TestCase):
    def test_without_solo_unlock_and_sensitive_paths_still_hold(self) -> None:
        reasons = human_reasons([".github/workflows/ci.yml"], UNLOCK, _config())
        self.assertEqual(len(reasons), 2, reasons)

    def test_solo_keeps_the_unlock_as_trail_but_does_not_hold(self) -> None:
        self.assertEqual(human_reasons(["tests/test_x.py", ".github/workflows/ci.yml"], UNLOCK, _config(solo="on")), [])

    def test_solo_honours_an_explicit_always_human_list(self) -> None:
        reasons = human_reasons([".github/workflows/ci.yml"], UNLOCK, _config(solo="on", alwaysHuman=[".github/**"]))
        self.assertEqual(reasons, ["toca caminho alwaysHuman: .github/workflows/ci.yml"])

    def test_explicit_empty_always_human_turns_paths_off_without_solo(self) -> None:
        self.assertEqual(human_reasons(["package-lock.json"], "", _config(alwaysHuman=[])), [])

    def test_unchecked_paths_still_stop_in_solo(self) -> None:
        self.assertEqual(human_reasons(None, "", _config(solo="on")), ["caminhos do PR nao conferidos pelo git"])


class AutoFinishTests(unittest.TestCase):
    def test_solo_adds_feature_to_the_kinds(self) -> None:
        self.assertNotIn("feature", settings(_config())["kinds"])
        self.assertIn("feature", settings(_config(solo="on"))["kinds"])

    def test_solo_feature_with_approved_audit_closes(self) -> None:
        task = {"id": "D-001", "kind": "feature", "audit": {"result": "approved"}}
        checks = _checks(task, _config(solo="on"))
        self.assertTrue(all(c["ok"] for c in checks.values()), checks)
        self.assertIn("solo", checks["achados da auditoria"]["evidence"])

    def test_without_solo_feature_and_missing_counts_still_wait(self) -> None:
        task = {"id": "D-001", "kind": "feature", "audit": {"result": "approved"}}
        checks = _checks(task, _config())
        self.assertFalse(checks["tipo permitido"]["ok"])
        self.assertFalse(checks["achados da auditoria"]["ok"])

    def test_solo_still_counts_recorded_findings(self) -> None:
        task = {"id": "D-001", "kind": "chore", "audit": {"result": "approved", "openFindings": {"BLOQUEANTE": 1}}}
        self.assertFalse(_checks(task, _config(solo="on"))["achados da auditoria"]["ok"])


class ConfigureTests(unittest.TestCase):
    def _ctx(self, config: dict) -> Context:
        return Context([], config, CORE_SRC)

    def test_solo_step_recommends_off_and_only_the_owner_turns_it_on(self) -> None:
        step = STEPS_BY_ID["autonomy-solo"]
        self.assertEqual(step.recommend(self._ctx(_config()))[0], "off")
        self.assertIn("O QUE SE PERDE", step.explain)

    def test_solo_makes_locks_and_kinds_steps_moot(self) -> None:
        for step_id in ("always-human-locks", "auto-finish-kinds"):
            self.assertTrue(STEPS_BY_ID[step_id].applies(self._ctx(_config())), step_id)
            self.assertFalse(STEPS_BY_ID[step_id].applies(self._ctx(_config(solo="on"))), step_id)


if __name__ == "__main__":
    unittest.main()
