"""D-172: so a marca no inicio da linha desbloqueia, para a fila e para o ship.

A mensagem da D-167 contava a historia do bug citando a marca no meio de uma
frase; a fila leu como desbloqueio e parou no dono. A marca de verdade e a
linha que o `commit-message` escreve: `[unlock:<trava>] motivo: ...`.
"""

from __future__ import annotations

import unittest

from conftest_paths import ensure_core_importable

ensure_core_importable()

import _autonomy  # noqa: E402
from _commit import unlock_marks  # noqa: E402

REAL = "🐛 fix(D-001): x\n\ncorpo\n\n[unlock:testes-sao-contrato] motivo: autorizado\n"
CITED = "🐛 fix(D-001): x\n\nNa D-157 a marca [unlock:testes-sao-contrato] estava num commit vazio.\n"


class UnlockMarkTests(unittest.TestCase):
    def test_only_the_mark_that_starts_a_line_counts(self) -> None:
        self.assertEqual(unlock_marks(REAL), {"testes-sao-contrato"})
        self.assertEqual(unlock_marks(CITED), set())
        self.assertEqual(unlock_marks("  [UNLOCK:Foo] motivo: y"), {"foo"}, "indentada e maiuscula valem")

    def test_queue_does_not_stop_on_a_cited_mark(self) -> None:
        config = {"autonomy": {"alwaysHumanLocks": "*"}}
        self.assertEqual(_autonomy.human_reasons(["core/x.py"], CITED, config), [])
        self.assertEqual(_autonomy.human_reasons(["core/x.py"], REAL, config),
                         ["desbloqueia trava: testes-sao-contrato"])


if __name__ == "__main__":
    unittest.main()
