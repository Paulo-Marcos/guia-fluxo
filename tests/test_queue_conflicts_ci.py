"""D-169: CI vermelho logo depois da atualizacao da fila e conflito para o gerente.

O rebase da fila pode passar e o CI reprovar - conflito que o git nao ve
(visto na D-151: o arquivo gerado ficou com o partial antigo). Se o executor
atualizou a branch nesta passada, com `conflicts = manager` o item fica na fila
em `conflict`; sem atualizacao, check vermelho continua voltando ao autor.
"""

from __future__ import annotations

import json
import unittest

import test_queue_conflicts as base

A, B = base.A, base.B


class CiAfterQueueUpdateTests(base.QueueConflictTests):
    def test_red_ci_right_after_the_update_is_a_conflict(self) -> None:
        self._queued("D-001", 1, mergeState="BEHIND", afterUpdate={"head": B, "checks": "fail"},
                      patchIds={A: "pid-a", B: "pid-a"})
        self._queued("D-002", 2)
        self._ok("queue", "run")
        item = self._items()["D-001"]
        self.assertEqual(item["state"], "conflict")
        self.assertIn("depois da atualizacao da fila", item["conflictReason"])
        self.assertEqual(self._status("D-002"), "Integrada", "a fila segue")

    def test_red_ci_without_an_update_still_returns(self) -> None:
        self._queued("D-001", 1, checks="fail")
        self._ok("queue", "run")
        self.assertEqual(self._status("D-001"), "Em desenvolvimento")
        self.assertNotIn("D-001", self._items())

    def test_default_returns_even_after_an_update(self) -> None:
        (self.sb / ".guia" / "process.json").write_text(json.dumps({"delivery": {"mode": "pr"}}), encoding="utf-8")
        self._queued("D-001", 1, mergeState="BEHIND", afterUpdate={"head": B, "checks": "fail"},
                      patchIds={A: "pid-a", B: "pid-a"})
        self._ok("queue", "run")
        self.assertEqual(self._status("D-001"), "Em desenvolvimento")


if __name__ == "__main__":
    unittest.main()
