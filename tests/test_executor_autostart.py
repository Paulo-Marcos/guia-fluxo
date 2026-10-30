"""D-204: no pilot, o chat que enfileira liga a fila - sem chat so para o `queue run`.

O dono decidiu que o nivel pilot ja autoriza (sem chave nova). `queue add`
grava o item e SO DEPOIS le o lease: executor vivo -> nada; sem lease -> sobe
`queue run` destacado. O executor solta o lease e SO DEPOIS rele a fila: item
que chegou na janela e integrado por ele. Dois chats ao mesmo tempo nunca
deixam dois executores integrando (o `O_EXCL` do lease, D-127).

Aqui o spawn e de verdade (o conftest o desliga para os outros testes): o
executor destacado integra contra o GitHub roteirizado do fixture.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

from conftest_paths import CORE_LOCK, CORE_SRC

A = "a" * 40
WAIT_SECONDS = 90.0


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class AutostartTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.sb = Path(self._tmp.name)
        (self.sb / "core" / "src").mkdir(parents=True)
        (self.sb / "core" / "lock").mkdir(parents=True)
        for src in CORE_SRC.glob("*.py"):
            if not src.name.startswith("__"):
                shutil.copy2(src, self.sb / "core" / "src" / src.name)
        shutil.copy2(CORE_LOCK / "lock_api.py", self.sb / "core" / "lock" / "lock_api.py")
        (self.sb / ".guia").mkdir()
        self._process("pilot")
        # Remoto de verdade: o `queue add` confere os caminhos do PR pelo git (D-134);
        # sem isso o alwaysHuman segura o item e o pilot nao teria o que integrar.
        (self.sb / ".gitignore").write_text(".guia/\ncore/\ndriver.py\n", encoding="utf-8")
        (self.sb / "app.txt").write_text("app\n", encoding="utf-8")
        remote = self.sb.parent / f"{self.sb.name}-remote.git"
        self.addCleanup(shutil.rmtree, remote, True)
        self._git("init", "-q", "--bare", str(remote))
        for args in (("init", "-q", "-b", "main"), ("add", "."), ("commit", "-q", "-m", "init"),
                     ("remote", "add", "origin", str(remote)), ("push", "-q", "-u", "origin", "main")):
            self._git(*args)
        self.fixture = self.sb / "gh.json"
        self.fixture.write_text(json.dumps({"__auth__": True}), encoding="utf-8")
        self.prs: list[dict] = []
        for title in ("primeira", "segunda"):
            self._ok("feature", title)

    def tearDown(self) -> None:
        self._wait(lambda: not self._lease().exists(), "executor solto no fim do teste")
        self._tmp.cleanup()

    def _git(self, *args: str) -> None:
        result = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=self.sb,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, msg=f"git {args}: {result.stderr}")

    def _branch(self, number: int) -> None:
        """Branch do PR no remoto, mudando so um arquivo comum (nada que pare no dono)."""
        self._git("checkout", "-q", "-b", f"b{number}")
        (self.sb / f"app{number}.txt").write_text("mudou\n", encoding="utf-8")
        self._git("add", f"app{number}.txt")
        self._git("commit", "-q", "-m", f"pr {number}")
        self._git("push", "-q", "origin", f"b{number}")
        self._git("checkout", "-q", "main")

    def _process(self, level: str) -> None:
        (self.sb / ".guia" / "process.json").write_text(json.dumps(
            {"delivery": {"mode": "pr"}, "autonomy": {"default": level, "ceiling": "pilot"}}), encoding="utf-8")

    def _env(self, auto: str = "on") -> dict[str, str]:
        return {**os.environ, "GUIA_GH_FIXTURE": str(self.fixture), "GUIA_AUTO_EXECUTOR": auto}

    def _cmd(self, *args: str) -> list[str]:
        return [sys.executable, "core/src/guia.py", *args]

    def _run(self, *args: str, auto: str = "on") -> subprocess.CompletedProcess[str]:
        return subprocess.run(self._cmd(*args), cwd=self.sb, capture_output=True, text=True,
                              encoding="utf-8", env=self._env(auto))

    def _ok(self, *args: str, auto: str = "on") -> subprocess.CompletedProcess[str]:
        result = self._run(*args, auto=auto)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def _ready_for_queue(self, task_id: str, number: int) -> None:
        """Demanda auditada no head A, Em PR, com o PR roteirizado (CLEAN, checks verdes)."""
        self._branch(number)
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
            f"✨ feat({task_id}): titulo\n\ncorpo\n", encoding="utf-8")
        self.prs.append({"number": number, "head": A, "state": "OPEN", "mergeState": "CLEAN",
                         "checks": "pass", "patchIds": {A: "pid-a"}})
        Path(str(self.fixture) + ".prs.json").write_text(json.dumps(self.prs), encoding="utf-8")

    def _status(self, task_id: str) -> str:
        tasks = json.loads((self.sb / ".guia" / "tasks.json").read_text(encoding="utf-8"))["tasks"]
        return next(t for t in tasks if t["id"] == task_id)["status"]

    def _lease(self) -> Path:
        return self.sb / ".guia" / "queue" / "executor.lease"

    def _log(self) -> str:
        path = self.sb / ".guia" / "queue" / "executor-auto.log"
        return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""

    def _wait(self, condition, what: str) -> None:
        deadline = time.monotonic() + WAIT_SECONDS
        while not condition():
            if time.monotonic() > deadline:
                self.fail(f"{what}: estourou {WAIT_SECONDS:.0f}s. Log do executor:\n{self._log()}")
            time.sleep(0.2)

    def test_pilot_queue_add_starts_the_executor_that_integrates(self) -> None:
        self._ready_for_queue("D-001", 1)
        out = self._ok("queue", "add", "D-001").stdout
        self.assertIn("Executor ligado pelo pilot", out)
        self._wait(lambda: self._status("D-001") == "Integrada", "o executor ligado pelo chat integra")
        self._wait(lambda: not self._lease().exists(), "o executor solta o lease ao sair")

    def test_live_executor_means_nothing_is_started(self) -> None:
        self._ready_for_queue("D-001", 1)
        self._lease().write_text(json.dumps({"pid": 4242, "host": "maquina", "heartbeat": time.time()}),
                                 encoding="utf-8")
        out = self._ok("queue", "add", "D-001").stdout
        self.assertIn("Executor ja ativo (pid 4242", out)
        self.assertEqual(self._log(), "", "nenhum executor subiu")
        self._lease().unlink()

    def test_below_pilot_the_queue_stays_with_the_owner(self) -> None:
        self._process("queue")
        self._ready_for_queue("D-001", 1)
        out = self._ok("queue", "add", "D-001").stdout
        self.assertNotIn("Executor ligado", out)
        self.assertEqual(self._log(), "")
        self.assertEqual(self._status("D-001"), "Na fila")

    def test_paused_queue_is_not_started(self) -> None:
        self._ready_for_queue("D-001", 1)
        self._ok("queue", "pause", "--reason", "manutencao")
        out = self._ok("queue", "add", "D-001").stdout
        self.assertIn("Executor nao ligado: fila parada (manutencao)", out)
        self.assertEqual(self._log(), "")

    def test_next_restarts_an_executor_that_left_the_item_waiting(self) -> None:
        self._ready_for_queue("D-001", 1)
        self._ok("queue", "add", "D-001", auto="off")  # executor que ja saiu: nada vivo
        step = json.loads(self._ok("next", "D-001", "--json").stdout)
        self.assertIn("Executor ligado pelo pilot", step["executor"])
        self.assertIn("sem executor ativo", step["why"])
        self.assertIn("acompanhe com `guia next D-001`", step["why"])
        self._wait(lambda: self._status("D-001") == "Integrada", "o executor religado pelo next integra")

    def test_two_chats_at_once_integrate_both_with_one_executor_at_a_time(self) -> None:
        """Sessao A e sessao B prontas ao mesmo tempo: ambas chamam a fila."""
        self._ready_for_queue("D-001", 1)
        self._ready_for_queue("D-002", 2)
        chats = [subprocess.Popen(self._cmd("queue", "add", task_id), cwd=self.sb, env=self._env(),
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")
                 for task_id in ("D-001", "D-002")]
        outs = [chat.communicate(timeout=WAIT_SECONDS)[0] for chat in chats]
        for chat, out in zip(chats, outs):
            self.assertEqual(chat.returncode, 0, msg=out)
            said = ("Executor ligado pelo pilot", "Executor ja ativo", "ainda subindo")
            self.assertTrue(any(line in out for line in said), out)
        self._wait(lambda: {self._status("D-001"), self._status("D-002")} == {"Integrada"},
                   "os dois itens integrados")
        self._wait(lambda: not self._lease().exists(), "executores sairam")
        log = self._log()
        for task_id in ("D-001", "D-002"):
            self.assertEqual(log.count(f"{task_id}: integrada"), 1, f"{task_id} integrada uma vez so:\n{log}")
        queue = json.loads((self.sb / ".guia" / "queue.json").read_text(encoding="utf-8"))
        self.assertEqual(queue["items"], [])

    def test_item_enqueued_while_the_executor_leaves_is_not_orphaned(self) -> None:
        """A corrida: o executor achou a fila vazia; antes de soltar o lease, o
        chat B enfileira, ve o lease vivo e nao sobe ninguem. O executor solta
        o lease, rele a fila e integra o item de B."""
        self._ready_for_queue("D-001", 1)
        self._ready_for_queue("D-002", 2)
        driver = self.sb / "driver.py"
        driver.write_text(textwrap.dedent(f"""
            import subprocess, sys
            sys.path.insert(0, "core/src")
            import _executor

            real, calls = _executor._pass, []

            def racing_pass(config, tried, once):
                calls.append(1)
                if len(calls) == 1:  # fila vazia; o lease ainda e deste executor
                    out = subprocess.run([sys.executable, "core/src/guia.py", "queue", "add", "D-002"],
                                         capture_output=True, text=True, encoding="utf-8").stdout
                    print("CHAT B:", out)
                    return 0, _executor.PASS_EMPTY
                return real(config, tried, once)

            _executor._pass = racing_pass
            print("INTEGRADOS", _executor.run({{"delivery": {{"mode": "pr"}}}}))
        """), encoding="utf-8")
        result = subprocess.run([sys.executable, str(driver)], cwd=self.sb, capture_output=True, text=True,
                                encoding="utf-8", env=self._env())
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("Executor ja ativo", result.stdout, "B viu o lease vivo e nao subiu ninguem")
        self.assertIn("retomando", result.stdout)
        self.assertIn("INTEGRADOS 1", result.stdout)
        self.assertEqual(self._status("D-002"), "Integrada")
        self.assertEqual(self._log(), "", "so o executor que saia integrou")
        self.assertFalse(self._lease().exists())


if __name__ == "__main__":
    unittest.main()
