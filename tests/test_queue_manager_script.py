"""D-165: o roteiro do gerente da fila (`/guia:queue-control run`).

O comando continua so do usuario; o `run` faz deste chat o gerente: roda o
executor, resolve os conflitos que ele deixa na fila (rebase preservando as
duas intencoes, portao, auditoria do delta, ship, de volta a fila) e entrega
ao dono so o que pede decisao - sempre com o chat da demanda.
"""

from __future__ import annotations

import unittest

import yaml

from conftest_paths import REPO_ROOT

COMMAND = REPO_ROOT / "plugins" / "guia" / "commands" / "queue-control.md"


class QueueManagerScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = COMMAND.read_text(encoding="utf-8")
        self.front = yaml.safe_load(self.text.split("---", 2)[1])

    def test_still_user_only(self) -> None:
        self.assertIs(self.front.get("disable-model-invocation"), True)

    def test_loop_resolves_conflicts_and_requeues(self) -> None:
        for step in ("queue run", "queue --json", "conflito:", "worktree add <D-NNN>", "git rebase origin/main",
                     "preserving the intent of both sides", "--force-with-lease", "ship <D-NNN>",
                     "audit <D-NNN>", "delta mode", "queue add <D-NNN>"):
            self.assertIn(step, self.text, step)

    def test_hands_real_decisions_to_the_owner_with_the_chat(self) -> None:
        for rule in ("want opposite things", "locked file the PR did not already touch", "BLOQUEANTE", "chat <D-NNN>"):
            self.assertIn(rule, self.text, rule)

    def test_keeps_the_principles(self) -> None:
        self.assertIn("Never `approve`, `finish` or `autonomy` on your own", self.text)
        self.assertIn("[unlock:]", self.text, "a marca fica no commit que toca o arquivo")
        self.assertIn("never bypassed", self.text)


if __name__ == "__main__":
    unittest.main()
