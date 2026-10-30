"""D-210: achados da auditoria do PR #100 sobre o quadro do controlador.

`--from` sem status nascia em DEV sem sessao (ocupava vaga e sumia das
propostas); pergunta e citacao vazias eram aceitas; `answer --by self`
passava; Planejada com sessao aberta sumia do quadro; `--archived` valia em
demanda nao concluida e junto com `--unarchived`; Resolvida contava como
ativa; Integrada saia do quadro antes do `finish` do dono.
"""

from __future__ import annotations

import unittest
from unittest import mock

import test_controller_board as board_tests

import _controller  # noqa: E402

CONTROLLER, EXECUTOR, OTHER = board_tests.CONTROLLER, board_tests.EXECUTOR, board_tests.OTHER


class AuditFixesCliTests(board_tests.ControllerBoardCliTests):
    # Reaproveita o sandbox; nao repete os testes da classe base.
    test_board_lists_executor_with_stage_and_ball = None
    test_question_queue_shows_together_and_answer_comes_back_quoted = None
    test_follow_up_is_proposed_with_the_inherited_controller = None
    test_done_executor_is_proposed_for_archive_until_recorded = None
    test_limit_from_config_counts_open_executors = None

    def test_from_without_status_is_born_planned_not_in_dev(self) -> None:
        self._ok("bug", "Sem status", "--from", "D-001")
        self.assertEqual(self._task("D-002")["status"], "Planejada")
        self.assertIn("PROPOSTA D-002 Planejada", self._ok("controle"))

    def test_empty_question_quote_and_bad_session_are_refused(self) -> None:
        self.assertNotEqual(self._run("ask", "D-001", "  ").returncode, 0)
        self._ok("ask", "D-001", "Pergunta?")
        self.assertNotEqual(self._run("answer", "D-001", "P1", "--quote", " ").returncode, 0)
        self.assertNotEqual(self._run("answer", "D-001", "P1", "--quote", "sim", "--by", "self").returncode, 0)
        self.assertIsNone(self._task("D-001")["decisions"][0]["answer"])

    def test_planned_demand_with_a_session_is_an_executor_and_takes_a_slot(self) -> None:
        self._ok("chore", "Aberta", "--status", "planned", "--from", "D-001")
        self._ok("chat", "D-002", "--title", "D-002", "--session", OTHER, "--controller", CONTROLLER)
        out = self._ok("controle")
        self.assertIn("executoras 2 de 4", out)
        self.assertIn("D-002 🧹 Planejada", out)
        self.assertNotIn("PROPOSTA D-002", out)

    def test_archive_only_done_demands_and_flags_are_exclusive(self) -> None:
        refused = self._run("chat", "D-001", "--archived")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("so se arquiva", refused.stdout + refused.stderr)
        self.assertNotEqual(self._run("chat", "D-001", "--archived", "--unarchived").returncode, 0)


class DoneStatusesTests(unittest.TestCase):
    def test_integrated_stays_on_the_board_for_the_owner_finish_and_resolved_is_done(self) -> None:
        tasks = [{"id": "D-001", "status": "Integrada", "chat": {"session": EXECUTOR, "controller": CONTROLLER}},
                 {"id": "D-002", "status": "Resolvida", "chat": {"session": OTHER, "controller": CONTROLLER}}]
        step = {"step": "stop", "why": "integrada; valide no uso e rode o finish", "owner": "dono"}
        with mock.patch.object(_controller, "next_step", return_value=step):
            block = _controller.board(tasks, {}, CONTROLLER)[0]
        self.assertEqual([(r["task"], r["ball"]) for r in block["executors"]], [("D-001", "dono")])
        self.assertEqual([a["task"] for a in block["archive"]], ["D-002"])


if __name__ == "__main__":
    unittest.main()
