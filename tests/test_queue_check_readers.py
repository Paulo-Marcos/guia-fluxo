"""D-201: os dois leitores de check do motor da fila, contra o que o `gh` responde.

Medido no `backend-simulators` em 29/10/2026 (plugin 0.11.0), num repositorio
**sem protecao de branch** (plano Pro exigido no privado; a trava de la e um
hook `pre-push`):

    gh pr checks 4 --required  ->  rc=1, "no required checks reported on the '<branch>' branch"
    gh pr checks 4             ->  rc=0, [{"bucket":"pass","name":"CI ok"},{"bucket":"pass","name":"backend"}]

Sem check obrigatorio o array nao vem, a lista fica vazia e o `if checks and
all(...)` nunca e verdade: o veredito era `pending` para sempre e **nenhum item
mergeava** (40 min por item, com `estado CLEAN, checks pending` na fila).

E quatro merges na main em 21 s, com `cancel-in-progress: true` no consumidor:

    4ba20a2 completed/cancelled | 887612e completed/cancelled
    6db9048 completed/cancelled | fd0b884 completed/success

`cancelled` fora da lista permitida contava como falha e **congelava a fila**
com "main vermelha" - a main estava verde. Run cancelado e ausencia de prova,
nao prova de falha.
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

from conftest_paths import CORE_LOCK, CORE_SRC, ensure_core_importable

ensure_core_importable()

import _github  # noqa: E402

A = "a" * 40
SEM_OBRIGATORIOS = "no required checks reported on the 'd-023-acertar-o-registro' branch"
SEM_CHECK_ALGUM = "no checks reported on the 'd-023-acertar-o-registro' branch"
VERDES = [{"bucket": "pass", "name": "CI ok"}, {"bucket": "pass", "name": "backend"}]


def _run(returncode: int = 0, stdout: object = "", stderr: str = "") -> _github.GhRun:
    payload = json.dumps(stdout) if isinstance(stdout, list) else stdout
    return _github.GhRun(returncode, payload, stderr)


def _never() -> _github.GhRun:
    raise AssertionError("o leitor consultou os checks sem filtro sem precisar")


class PrChecksReaderTests(unittest.TestCase):
    """`gh pr checks`: o que vale como liberacao para o merge."""

    def test_obrigatorios_verdes_liberam_sem_consultar_o_resto(self) -> None:
        reading = _github.read_pr_checks(_run(stdout=VERDES), _never)
        self.assertEqual(reading.verdict, "pass")
        self.assertEqual(reading.case, _github.CASE_REQUIRED)

    def test_obrigatorio_vermelho_reprova_pelo_nome(self) -> None:
        vermelho = [{"bucket": "fail", "name": "CI ok"}, {"bucket": "pass", "name": "backend"}]
        reading = _github.read_pr_checks(_run(stdout=vermelho), _never)
        self.assertEqual((reading.verdict, reading.failing), ("fail", ["CI ok"]))

    def test_obrigatorio_ainda_rodando_continua_pendente(self) -> None:
        rodando = [{"bucket": "pending", "name": "CI ok"}, {"bucket": "pass", "name": "backend"}]
        reading = _github.read_pr_checks(_run(stdout=rodando), _never)
        self.assertEqual(reading.verdict, "pending")
        self.assertEqual(reading.case, _github.CASE_REQUIRED)

    def test_sem_politica_de_obrigatorios_julga_pelo_que_rodou(self) -> None:
        """O caso do backend-simulators: nada e obrigatorio, mas o CI rodou e passou."""
        reading = _github.read_pr_checks(
            _run(returncode=1, stderr=SEM_OBRIGATORIOS), lambda: _run(stdout=VERDES)
        )
        self.assertEqual(reading.verdict, "pass")
        self.assertEqual(reading.case, _github.CASE_NO_POLICY)
        self.assertIn("sem politica", reading.detail)

    def test_sem_politica_com_check_vermelho_nao_libera(self) -> None:
        """Cair para o que rodou nao pode virar merge no vermelho."""
        misto = [{"bucket": "pass", "name": "CI ok"}, {"bucket": "fail", "name": "backend"}]
        reading = _github.read_pr_checks(
            _run(returncode=1, stderr=SEM_OBRIGATORIOS), lambda: _run(stdout=misto)
        )
        self.assertEqual((reading.verdict, reading.failing), ("fail", ["backend"]))

    def test_sem_politica_com_check_rodando_espera(self) -> None:
        rodando = [{"bucket": "pass", "name": "CI ok"}, {"bucket": "pending", "name": "backend"}]
        reading = _github.read_pr_checks(
            _run(returncode=1, stderr=SEM_OBRIGATORIOS), lambda: _run(stdout=rodando)
        )
        self.assertEqual(reading.verdict, "pending")
        self.assertEqual(reading.case, _github.CASE_NO_POLICY)

    def test_nenhum_check_reportou_e_estado_proprio(self) -> None:
        """Sem check algum != obrigatorios atrasados: esperar nao muda um; muda o outro."""
        reading = _github.read_pr_checks(
            _run(returncode=1, stderr=SEM_CHECK_ALGUM), lambda: _run(returncode=1, stderr=SEM_CHECK_ALGUM)
        )
        self.assertEqual(reading.verdict, "pending")
        self.assertEqual(reading.case, _github.CASE_SILENT)
        self.assertIn("nenhum check", reading.detail)

    def test_strict_nao_cai_para_o_que_rodou(self) -> None:
        """Quem exige protecao de verdade continua esperando, e o log diz por que."""
        reading = _github.read_pr_checks(
            _run(returncode=1, stderr=SEM_OBRIGATORIOS), lambda: _run(stdout=VERDES),
            policy=_github.CHECKS_STRICT,
        )
        self.assertEqual(reading.verdict, "pending")
        self.assertIn("strict", reading.detail)

    def test_erro_do_gh_nao_vira_check_verde(self) -> None:
        reading = _github.read_pr_checks(
            _run(returncode=1, stderr="gh: Not Found (HTTP 404)"), lambda: _run(returncode=1, stderr="x")
        )
        self.assertEqual(reading.verdict, "pending")
        self.assertEqual(reading.case, _github.CASE_GH_ERROR)
        self.assertIn("404", reading.detail)


class NoChecksPolicyTests(unittest.TestCase):
    """Repositorio que nunca reporta check: decisao explicita, nao acidente."""

    def _silent(self) -> _github.ChecksReading:
        return _github.read_pr_checks(
            _run(returncode=1, stderr=SEM_CHECK_ALGUM), lambda: _run(returncode=1, stderr=SEM_CHECK_ALGUM)
        )

    def test_padrao_espera_e_diz_o_motivo(self) -> None:
        settled = _github.settle(self._silent(), _github.NO_CHECKS_WAIT)
        self.assertEqual(settled.verdict, "pending")
        self.assertIn("nenhum check", settled.detail)

    def test_merge_so_quando_o_dono_liga(self) -> None:
        settled = _github.settle(self._silent(), _github.NO_CHECKS_MERGE)
        self.assertEqual(settled.verdict, "pass")
        self.assertIn("noChecks=merge", settled.detail)

    def test_noChecks_nao_libera_quem_tem_check_vermelho(self) -> None:
        reading = _github.read_pr_checks(
            _run(returncode=1, stderr=SEM_OBRIGATORIOS),
            lambda: _run(stdout=[{"bucket": "fail", "name": "backend"}]),
        )
        self.assertEqual(_github.settle(reading, _github.NO_CHECKS_MERGE).verdict, "fail")


class CommitRunsReaderTests(unittest.TestCase):
    """`gh run list --commit`: o que conta como main vermelha."""

    @staticmethod
    def _runs(*pairs: tuple[str, str]) -> list[dict[str, str]]:
        return [{"name": name, "status": "completed", "conclusion": conclusion} for name, conclusion in pairs]

    def test_tudo_verde_passa(self) -> None:
        self.assertEqual(_github.read_commit_runs(self._runs(("backend", "success"))).verdict, "pass")

    def test_failure_ainda_reprova(self) -> None:
        reading = _github.read_commit_runs(self._runs(("backend", "failure")))
        self.assertEqual((reading.verdict, reading.failing), ("fail", ["backend"]))

    def test_timeout_ainda_reprova(self) -> None:
        self.assertEqual(_github.read_commit_runs(self._runs(("backend", "timed_out"))).verdict, "fail")

    def test_run_cancelado_nao_e_reprovado(self) -> None:
        """4ba20a2: cancelado pelo cancel-in-progress do merge seguinte. A main estava verde."""
        reading = _github.read_commit_runs(self._runs(("backend", "cancelled")))
        self.assertNotEqual(reading.verdict, "fail")
        self.assertEqual(reading.failing, [])

    def test_run_cancelado_e_ausencia_de_prova_nao_aprovacao(self) -> None:
        reading = _github.read_commit_runs(self._runs(("CI ok", "success"), ("backend", "cancelled")))
        self.assertEqual(reading.verdict, "pending")
        self.assertIn("cancel", reading.detail)
        self.assertIn("backend", reading.detail)

    def test_stale_conta_como_cancelado(self) -> None:
        self.assertEqual(_github.read_commit_runs(self._runs(("backend", "stale"))).verdict, "pending")

    def test_vermelho_ao_lado_de_cancelado_ainda_reprova(self) -> None:
        reading = _github.read_commit_runs(self._runs(("CI ok", "cancelled"), ("backend", "failure")))
        self.assertEqual((reading.verdict, reading.failing), ("fail", ["backend"]))

    def test_run_em_andamento_fica_pendente(self) -> None:
        runs = [{"name": "backend", "status": "in_progress", "conclusion": None}]
        self.assertEqual(_github.read_commit_runs(runs).verdict, "pending")

    def test_sem_run_algum_fica_pendente(self) -> None:
        self.assertEqual(_github.read_commit_runs([]).verdict, "pending")


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class QueueEndToEndTests(unittest.TestCase):
    """A fila inteira contra o `gh` roteirizado com as respostas medidas."""

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
        self.process = {"delivery": {"mode": "pr"}}
        self._save_process()
        self.fixture = self.sb / "gh.json"
        self.fixture.write_text(json.dumps({"__auth__": True}), encoding="utf-8")
        self.prs: list[dict] = []
        self._ok("feature", "primeira")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _save_process(self) -> None:
        (self.sb / ".guia" / "process.json").write_text(json.dumps(self.process), encoding="utf-8")

    def _run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "core/src/guia.py", *args],
            cwd=self.sb, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "GUIA_GH_FIXTURE": str(self.fixture), "PYTHONUTF8": "1"},
        )

    def _ok(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = self._run_cli(*args)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def _queued(self, task_id: str, number: int, **pr) -> None:
        path = self.sb / ".guia" / "tasks.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for task in data["tasks"]:
            if task["id"] == task_id:
                task["status"] = "Em PR"
                task["pr"] = {"number": number, "url": "u", "branch": f"b{number}", "head": A}
                task["audit"] = {"result": "approved", "auditedSha": A, "auditedPatchId": "pid-a"}
        path.write_text(json.dumps(data), encoding="utf-8")
        (self.sb / ".guia" / "queue").mkdir(exist_ok=True)
        (self.sb / ".guia" / "queue" / f"{task_id}.msg").write_text(
            f"✨ feat({task_id}): titulo\n\ncorpo do porque\n", encoding="utf-8"
        )
        self.prs.append({"number": number, "head": A, "state": "OPEN", "mergeState": "CLEAN",
                         "patchIds": {A: "pid-a"}, **pr})
        Path(str(self.fixture) + ".prs.json").write_text(json.dumps(self.prs), encoding="utf-8")
        self._ok("queue", "add", task_id)
        self._ok("approve", task_id)

    def _pr(self, number: int) -> dict:
        prs = json.loads(Path(str(self.fixture) + ".prs.json").read_text(encoding="utf-8"))
        return next(pr for pr in prs if pr["number"] == number)

    def _queue(self) -> dict:
        return json.loads((self.sb / ".guia" / "queue.json").read_text(encoding="utf-8"))

    def test_repo_sem_protecao_de_branch_integra(self) -> None:
        """O defeito que impediu todo merge: CLEAN + checks verdes, veredito `pending`."""
        self._queued("D-001", 1, ghChecks={
            "required": {"rc": 1, "stderr": SEM_OBRIGATORIOS},
            "plain": {"stdout": VERDES},
        })
        out = self._ok("queue", "run").stdout
        self.assertEqual(self._pr(1)["state"], "MERGED")
        self.assertEqual(self._pr(1)["merged"]["matchHead"], A)
        self.assertEqual(self._queue()["items"], [])
        self.assertIn("sem politica", out)

    def test_repo_sem_check_algum_fica_esperando(self) -> None:
        self.process["delivery"]["queue"] = {"ciTimeoutMinutes": 0.01}
        self._save_process()
        self._queued("D-001", 1, ghChecks={
            "required": {"rc": 1, "stderr": SEM_CHECK_ALGUM},
            "plain": {"rc": 1, "stderr": SEM_CHECK_ALGUM},
        })
        out = self._ok("queue", "run").stdout
        self.assertNotIn("merged", self._pr(1))
        self.assertEqual([i["id"] for i in self._queue()["items"]], ["D-001"])
        self.assertIn("nenhum check", out)
        log = " ".join(entry["msg"] for entry in self._queue()["items"][0].get("log") or [])
        self.assertIn("nenhum check", log)

    def test_repo_sem_check_algum_com_noChecks_merge_integra(self) -> None:
        """A decisao do dono, explicita no process.json - nao um acidente do leitor."""
        self.process["delivery"]["queue"] = {"ciTimeoutMinutes": 0.01, "noChecks": "merge"}
        self._save_process()
        self._queued("D-001", 1, ghChecks={
            "required": {"rc": 1, "stderr": SEM_CHECK_ALGUM},
            "plain": {"rc": 1, "stderr": SEM_CHECK_ALGUM},
        })
        out = self._ok("queue", "run").stdout
        self.assertEqual(self._pr(1)["state"], "MERGED")
        self.assertIn("noChecks=merge", out, "o log precisa dizer que foi a politica do dono que liberou")

    def test_main_com_run_cancelado_nao_congela_a_fila(self) -> None:
        """Tres runs cancelados em 21 s congelaram a fila tres vezes por um vermelho que nao existia."""
        self._queued("D-001", 1, squashSha="f" * 40, ghChecks={"required": {"stdout": VERDES}},
                     mainRuns=[{"name": "backend", "status": "completed", "conclusion": "cancelled"},
                               {"name": "CI ok", "status": "completed", "conclusion": "success"}])
        out = self._ok("queue", "run").stdout
        self.assertEqual(self._pr(1)["state"], "MERGED")
        self.assertIsNone(self._queue().get("frozenReason"))
        self.assertNotIn("FILA CONGELADA", out)
        self.assertIn("cancel", out, "o log precisa dizer que faltou prova, nao que a main esta verde")

    def test_main_vermelha_de_verdade_ainda_congela(self) -> None:
        self._queued("D-001", 1, squashSha="f" * 40, ghChecks={"required": {"stdout": VERDES}},
                     mainRuns=[{"name": "backend", "status": "completed", "conclusion": "failure"}])
        out = self._ok("queue", "run").stdout
        self.assertIn("FILA CONGELADA", out)
        self.assertIn("backend", self._queue()["frozenReason"])


if __name__ == "__main__":
    unittest.main()
