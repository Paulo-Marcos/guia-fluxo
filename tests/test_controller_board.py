"""D-210 (ADR-0025): o controlador coordena as sessoes e concentra as decisoes.

Na sessao controladora de 2026-10-30 (D-202 a D-209) as perguntas ao dono
chegaram uma a uma por mensagem, follow-ups surgiram fora do controlador,
sessoes concluidas acumularam na barra lateral e o controlador montou o estado
de tudo a partir de notas soltas. Agora o motor monta o quadro (`controle`),
guarda as perguntas na demanda (`ask`/`answer`), a follow-up nasce proposta
(`--from`), o quadro propoe arquivar as concluidas e conta as vagas.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from conftest_paths import CORE_LOCK, CORE_SRC, REPO_ROOT, ensure_core_importable

ensure_core_importable()

import _controller  # noqa: E402

EXECUTOR = "local_0000aaaa-1111-2222-3333-444455556666"
OTHER = "local_1111bbbb-1111-2222-3333-444455556666"
CONTROLLER = "local_9999ffff-8888-7777-6666-555544443333"
COMMANDS = REPO_ROOT / "plugins" / "guia" / "commands"


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class ControllerBoardCliTests(unittest.TestCase):
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
        self._process({"delivery": {"mode": "pr"}})
        self._ok("feature", "Mostrar a nota")
        self._ok("chat", "D-001", "--title", "D-001", "--session", EXECUTOR, "--controller", CONTROLLER)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _process(self, data: dict) -> None:
        (self.sb / ".guia" / "process.json").write_text(json.dumps(data), encoding="utf-8")

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, "core/src/guia.py", *args], cwd=self.sb, capture_output=True,
                              text=True, encoding="utf-8", env={**os.environ, "PYTHONUTF8": "1"})

    def _ok(self, *args: str) -> str:
        result = self._run(*args)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result.stdout

    def _task(self, task_id: str) -> dict:
        tasks = json.loads((self.sb / ".guia" / "tasks.json").read_text(encoding="utf-8"))["tasks"]
        return next(t for t in tasks if t["id"] == task_id)

    def test_board_lists_executor_with_stage_and_ball(self) -> None:
        out = self._ok("controle")
        self.assertIn(f"CONTROLADOR {CONTROLLER} - executoras 1 de 4 (3 vaga(s))", out)
        self.assertIn("D-001 ✨ Em desenvolvimento · bola: executora", out)
        block = json.loads(self._ok("controle", "--session", CONTROLLER, "--json"))[0]
        self.assertEqual((block["executors"][0]["task"], block["executors"][0]["session"]), ("D-001", EXECUTOR))

    def test_question_queue_shows_together_and_answer_comes_back_quoted(self) -> None:
        out = self._ok("ask", "D-001", "Teto de executoras?", "--option", "4", "--option", "6")
        self.assertIn("PERGUNTA D-001 P1 gravada", out)
        self._ok("ask", "D-001", "Planejada ou Backlog?")
        board = self._ok("controle")
        self.assertIn("bola: dono (2 pergunta(s) pendente(s))", board)
        self.assertIn("PERGUNTA D-001 P1: Teto de executoras? [opcoes: 4 | 6]", board)
        self.assertIn("PERGUNTA D-001 P2: Planejada ou Backlog?", board)

        out = self._ok("answer", "D-001", "p1", "--quote", "pode ser 4", "--by", CONTROLLER)
        self.assertIn(f'LEVE A EXECUTORA: {EXECUTOR} <- D-001 P1: o dono disse "pode ser 4"', out)
        decision = self._task("D-001")["decisions"][0]
        self.assertEqual((decision["askedBy"], decision["answer"]["quote"]), (EXECUTOR, "pode ser 4"))
        self.assertNotIn("PERGUNTA D-001 P1", self._ok("controle"))
        again = self._run("answer", "D-001", "P1", "--quote", "6")
        self.assertNotEqual(again.returncode, 0)
        self.assertIn("ja foi respondida", again.stdout + again.stderr)

    def test_follow_up_is_proposed_with_the_inherited_controller(self) -> None:
        out = self._ok("bug", "Achado no caminho", "--status", "planned", "--from", "D-001")
        self.assertIn(f"PROPOSTA: D-002 (de D-001) espera a sessao do controlador {CONTROLLER}", out)
        task = self._task("D-002")
        self.assertEqual((task["proposedFrom"], task["chat"]["controller"]), ("D-001", CONTROLLER))
        self.assertNotIn("session", task["chat"])
        self.assertIn("PROPOSTA D-002 Planejada (proposta por D-001): Achado no caminho - abra a sessao",
                      self._ok("controle"))
        refused = self._run("bug", "x", "--from", "D-999")
        self.assertNotEqual(refused.returncode, 0)

    def test_done_executor_is_proposed_for_archive_until_recorded(self) -> None:
        self._ok("feature", "Outra")
        self._ok("chat", "D-002", "--title", "D-002", "--session", OTHER, "--controller", CONTROLLER)
        self._ok("cancel", "D-002", "--reason", "nao precisa")
        self.assertIn(f"ARQUIVE COM OK DO DONO: {OTHER} (D-002 Cancelada) - depois: chat D-002 --archived",
                      self._ok("controle"))
        self.assertIn("SESSAO ARQUIVADA: D-002", self._ok("chat", "D-002", "--archived"))
        self.assertNotIn("ARQUIVE", self._ok("controle"))
        self._ok("chat", "D-002", "--unarchived")
        self.assertIn("ARQUIVE", self._ok("controle"))

    def test_limit_from_config_counts_open_executors(self) -> None:
        self._process({"delivery": {"mode": "pr"}, "controller": {"maxExecutors": 1}})
        self._ok("feature", "Outra")
        self._ok("chat", "D-002", "--title", "D-002", "--session", OTHER, "--controller", CONTROLLER)
        self._ok("chore", "Proposta", "--status", "planned", "--from", "D-001")
        out = self._ok("controle")
        self.assertIn("executoras 2 de 1 (0 vaga(s)) - ACIMA DO LIMITE", out)
        self.assertIn("PROPOSTA D-003 Planejada (proposta por D-001): Proposta - SEM VAGA", out)


class BallTests(unittest.TestCase):
    def _ball(self, step: dict, task: dict | None = None) -> str:
        with mock.patch.object(_controller, "next_step", return_value=step):
            return _controller.ball(task or {"id": "D-001", "status": "Na fila"}, {})[0]

    def test_queue_owners_mean_the_queue(self) -> None:
        self.assertEqual(self._ball({"step": "stop", "why": "x", "owner": "fila"}), "fila")
        self.assertEqual(self._ball({"step": "stop", "why": "x", "owner": "gerente da fila"}), "fila")

    def test_stop_for_the_agent_or_a_step_is_the_executor(self) -> None:
        self.assertEqual(self._ball({"step": "stop", "why": "x", "owner": "agente"}), "executora")
        self.assertEqual(self._ball({"step": "audit", "why": "x", "owner": None}), "executora")

    def test_stop_for_the_owner_and_open_question_are_the_owner(self) -> None:
        self.assertEqual(self._ball({"step": "stop", "why": "x", "owner": "dono"}), "dono")
        task = {"id": "D-001", "status": "Em PR", "decisions": [{"id": "P1", "answer": None}]}
        self.assertEqual(self._ball({"step": "audit", "why": "x", "owner": None}, task), "dono")

    def test_bad_limit_falls_back_to_default(self) -> None:
        self.assertEqual(_controller.max_executors({"controller": {"maxExecutors": 0}}), 4)
        self.assertEqual(_controller.max_executors({"controller": {"maxExecutors": 2}}), 2)


class ControllerRuleIsDocumentedTests(unittest.TestCase):
    def test_commands_and_agents_tell_both_roles_how(self) -> None:
        start = (COMMANDS / "start.md").read_text(encoding="utf-8")
        agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for text in (start, agents):
            for needle in ("guia controle", "--from", "ask", "answer", "--archived", "maxExecutors"):
                self.assertIn(needle, text)
        self.assertTrue((REPO_ROOT / "docs" / "adr" / "0025-controlador-concentra-as-decisoes.md").exists())


if __name__ == "__main__":
    unittest.main()
