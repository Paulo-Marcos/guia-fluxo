"""D-197: item em `conflict` na fila - o `next` aponta o passo real e o `ship` aceita.

Na D-190 o caminho do queue-control (passo 3) travou duas vezes: o `next`
respondia "na fila e aprovada" para um item em conflict (a aprovacao antiga
escondia o rebase/auditoria pendente), e o `ship` recusava a demanda `Na fila`
que o passo 3.4 manda atualizar. Agora o condutor olha o estado do item e o
`ship` aceita `Na fila` so com o item em conflict, mantendo a demanda na fila.
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

from conftest_paths import CORE_LOCK, CORE_SRC

A, B, C = "a" * 40, "b" * 40, "c" * 40


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=", *args],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8",
    )


def _copy_engine(dest: Path) -> None:
    dest.mkdir(parents=True)
    for src in CORE_SRC.glob("*.py"):
        if not src.name.startswith("__"):
            shutil.copy2(src, dest / src.name)
    shutil.copy2(CORE_LOCK / "lock_api.py", dest / "lock_api.py")


def _queue(guia: Path, state: str) -> None:
    (guia / "queue.json").write_text(json.dumps({"paused": False, "items": [
        {"id": "D-001", "pr": 1, "state": state, "conflictReason": "rebase com patch-id diferente",
         "auditedSha": A, "approval": {"by": "user"}}]}), encoding="utf-8")


def _set(guia: Path, **fields) -> None:
    path = guia / "tasks.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["tasks"][0].update(fields)
    path.write_text(json.dumps(data), encoding="utf-8")


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class ConflictNextTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.sb = Path(self._tmp.name)
        _copy_engine(self.sb / "core" / "src")
        subprocess.run(["git", "init", "-q"], cwd=self.sb, check=True, capture_output=True)
        self.guia = self.sb / ".guia"
        self.guia.mkdir()
        (self.guia / "process.json").write_text(json.dumps(
            {"delivery": {"mode": "pr"}, "autonomy": {"default": "pilot", "ceiling": "pilot"}}), encoding="utf-8")
        self.assertEqual(self._run("feature", "Mexer").returncode, 0)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, "core/src/guia.py", *args], cwd=self.sb,
                              capture_output=True, text=True, encoding="utf-8")

    def _next(self) -> dict:
        result = self._run("next", "D-001", "--json")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_conflict_is_not_approved_until_the_delta_is_audited(self) -> None:
        _set(self.guia, status="Na fila", pr={"number": 1, "head": A}, audit={"result": "approved", "auditedSha": A})
        _queue(self.guia, "conflict")
        step = self._next()
        self.assertEqual((step["step"], step["owner"]), ("stop", "gerente da fila"))
        self.assertNotIn("aprovada", step["why"])
        self.assertIn("rebase", step["why"])

    def test_audited_delta_goes_back_to_the_queue(self) -> None:
        _set(self.guia, status="Na fila", pr={"number": 1, "head": B}, audit={"result": "approved", "auditedSha": B})
        _queue(self.guia, "conflict")
        self.assertEqual(self._next()["step"], "queue-add", "delta auditado no head novo: volta a fila")
        _set(self.guia, pr={"number": 1, "head": C})
        self.assertEqual(self._next()["step"], "audit", "o head mudou depois da auditoria do delta")

    def test_waiting_item_keeps_the_old_answer(self) -> None:
        _set(self.guia, status="Na fila", pr={"number": 1, "head": A}, audit={"result": "approved", "auditedSha": A})
        _queue(self.guia, "waiting")
        step = self._next()
        self.assertEqual((step["step"], step["owner"]), ("stop", "fila"))


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class ConflictShipTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.engine = base / "plugin" / "bin"
        _copy_engine(self.engine)
        remote, self.main = base / "remote.git", base / "app"
        self.guia = self.main / ".guia"
        self.guia.mkdir(parents=True)
        (self.guia / "process.json").write_text(json.dumps({"delivery": {
            "mode": "pr", "commit": {"format": "gitmoji-conventional"},
            "changelog": {"style": "fragments"}, "gate": {"full": ["git --version"]}}}), encoding="utf-8")
        (self.main / ".gitignore").write_text(".guia/*\n!.guia/process.json\n", encoding="utf-8")
        (self.main / "app.txt").write_text("app\n", encoding="utf-8")
        _git(base, "init", "-q", "--bare", str(remote))
        for args in (("init", "-q", "-b", "main"), ("add", "."), ("commit", "-q", "-m", "init"),
                     ("remote", "add", "origin", str(remote)), ("push", "-q", "-u", "origin", "main")):
            self.assertEqual(_git(self.main, *args).returncode, 0, msg=str(args))
        self.fixture = base / "gh.json"
        self.fixture.write_text(json.dumps({"__auth__": True}), encoding="utf-8")
        self._ok(self.main, "feature", "Mostrar a nota")
        self._ok(self.main, "worktree", "add", "D-001")
        self.wt = base / "app-worktrees" / "d001"
        (self.wt / "app.txt").write_text("app com nota\n", encoding="utf-8")
        _git(self.wt, "add", "app.txt")
        _git(self.wt, "commit", "-q", "-m", "nota")
        self._ok(self.wt, "ready", "--file", "app.txt", "--request-test", "nota :: tests/test_nota.py")
        self._ok(self.wt, "changelog", "add", "--text", "Mostra a nota (D-001).")
        _git(self.wt, "add", "changelog.d")
        _git(self.wt, "commit", "-q", "-m", "fragmento")
        self._ok(self.wt, "ship", "--body", "v1")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(self.engine / "guia.py"), *args], cwd=cwd,
                              capture_output=True, text=True, encoding="utf-8",
                              env={**os.environ, "GUIA_GH_FIXTURE": str(self.fixture)})

    def _ok(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        result = self._run(cwd, *args)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def _status(self) -> str:
        return json.loads((self.guia / "tasks.json").read_text(encoding="utf-8"))["tasks"][0]["status"]

    def test_ship_refreshes_a_conflict_and_keeps_it_in_the_queue(self) -> None:
        _set(self.guia, status="Na fila")
        _queue(self.guia, "conflict")
        self._ok(self.wt, "ship", "--body", "v2")
        self.assertEqual(self._status(), "Na fila", "o queue add e que devolve o item a waiting")
        prs = json.loads(Path(str(self.fixture) + ".prs.json").read_text(encoding="utf-8"))
        self.assertIn("v2", prs[0]["body"])

    def test_ship_still_refuses_na_fila_outside_a_conflict(self) -> None:
        _set(self.guia, status="Na fila")
        _queue(self.guia, "waiting")
        result = self._run(self.wt, "ship", "--body", "v2")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Na fila", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
