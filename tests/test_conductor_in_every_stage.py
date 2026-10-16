"""D-177: o trilho do condutor esta no texto de toda etapa, nao so no ready.

No gerador-cortes os chats chamavam ready/ship/audit pelo terminal sem o texto
da skill ready - o unico que falava do `next` - e paravam para perguntar ou
mergeavam com gh por fora da fila. O texto do ready ainda abria como "handoff
para validacao humana", o que no pilot mandava parar.
"""

from __future__ import annotations

import unittest

from conftest_paths import REPO_ROOT

COMMANDS = REPO_ROOT / "plugins" / "guia" / "commands"


def _body(verb: str) -> str:
    return (COMMANDS / f"{verb}.md").read_text(encoding="utf-8")


class ConductorInEveryStageTests(unittest.TestCase):
    def test_creation_and_start_point_to_the_conductor(self) -> None:
        for verb in ("feature", "bug", "chore", "start"):
            body = _body(verb)
            self.assertIn("next <D-NNN> --json", body, verb)
            self.assertIn("do not ask the developer anything the step already answers", body, verb)
            self.assertIn("Never merge the PR yourself", body, verb)

    def test_ship_and_audit_carry_the_whole_conductor(self) -> None:
        for verb in ("ship", "audit"):
            body = _body(verb)
            self.assertIn("let the engine conduct", body, verb)
            self.assertIn("Never merge the PR yourself", body, verb)

    def test_ready_is_not_a_stop_above_manual(self) -> None:
        body = _body("ready")
        self.assertNotIn("you call `finish` afterward", body)
        self.assertIn("`ready` is NOT a stop", body)

    def test_new_files_under_a_modify_only_lock_need_no_unlock(self) -> None:
        body = _body("ship")
        self.assertIn("needs no mark and no question", body)
        self.assertIn("executor is alive", body)


if __name__ == "__main__":
    unittest.main()
