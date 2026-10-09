"""D-112: commit no formato gitmoji-conventional com [unlock:] automatico.

`delivery.commit.format = "gitmoji-conventional"` troca o header legado
(`chore(D-001): titulo`) por `<emoji> <tipo>(D-001): titulo`, com as marcas
`[unlock:<trava>] motivo: <motivo>` montadas pelas travas que os arquivos
declarados da demanda tocam (adicao, modificacao, delecao contra a base). O
motivo vem do agente e e obrigatorio. O verbo `commit-message` imprime a
mensagem (no modo `pr` o agente commita e monta o squash com ela).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import CORE_LOCK, CORE_SRC, ensure_core_importable

ensure_core_importable()

import _commit  # noqa: E402

REGISTRY = """version: 1
locks:
- id: homologado
  description: arquivo homologado
  operations: [modify, delete]
  files:
  - x.txt
- id: adicoes
  description: arquivo novo exige autorizacao
  operations: [add]
  files:
  - '*'
"""


class BuildMessageTests(unittest.TestCase):
    def _task(self, kind: str) -> dict:
        return {"id": "D-007", "kind": kind, "title": "fazer a coisa", "summary": ["porque sim"]}

    def test_kind_maps_to_emoji_and_type(self) -> None:
        cases = {"feature": "✨ feat", "bug": "🐛 fix", "chore": "🧹 chore"}
        for kind, prefix in cases.items():
            message = _commit.build_commit_message(self._task(kind), fmt="gitmoji-conventional")
            self.assertEqual(message.splitlines()[0], f"{prefix}(D-007): fazer a coisa")

    def test_trailers_and_co_author_close_the_message(self) -> None:
        message = _commit.build_commit_message(
            self._task("chore"),
            "o porque",
            fmt="gitmoji-conventional",
            trailers=["[unlock:a] motivo: m"],
            co_author="Agente <a@b>",
        )
        self.assertTrue(message.endswith("[unlock:a] motivo: m\n\nCo-Authored-By: Agente <a@b>"))
        self.assertIn("\n\no porque\n\n", message)
        self.assertNotIn("porque sim", message, "summary e bastidor, nao corpo")
        self.assertNotIn("Task: D-007", message)

    def test_legacy_is_the_default(self) -> None:
        message = _commit.build_commit_message(self._task("chore"))
        self.assertEqual(message.splitlines()[0], "chore(D-007): fazer a coisa")
        self.assertTrue(message.endswith("Task: D-007"))


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class CommitMessageVerbTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.sb = Path(self._tmp.name)
        (self.sb / "core" / "src").mkdir(parents=True)
        (self.sb / "core" / "lock").mkdir(parents=True)
        for src in CORE_SRC.glob("*.py"):
            if not src.name.startswith("__"):
                shutil.copy2(src, self.sb / "core" / "src" / src.name)
        for name in ("lock_api.py", "check-lock.py"):
            shutil.copy2(CORE_LOCK / name, self.sb / "core" / "lock" / name)
        (self.sb / ".guia" / "locks").mkdir(parents=True)
        (self.sb / ".guia" / "locks" / "registry.yaml").write_text(REGISTRY, encoding="utf-8")
        (self.sb / ".guia" / "process.json").write_text(
            json.dumps({"delivery": {"commit": {"format": "gitmoji-conventional", "coAuthor": "Agente <a@b>"}}}),
            encoding="utf-8",
        )
        (self.sb / ".gitignore").write_text(
            ".guia/*\n!.guia/process.json\n!.guia/locks/\ncore/\n", encoding="utf-8"
        )
        (self.sb / "x.txt").write_text("x\n", encoding="utf-8")
        for args in (
            ("init", "-q"),
            ("config", "user.email", "t@t"),
            ("config", "user.name", "t"),
            ("add", "."),
            ("commit", "-q", "-m", "seed"),
        ):
            self._git(*args)
        self._ok("chore", "mexer em x")
        (self.sb / "x.txt").write_text("x2\n", encoding="utf-8")
        (self.sb / "novo.txt").write_text("n\n", encoding="utf-8")
        self._ok("ready", "D-001", "--file", "x.txt", "--file", "novo.txt", "--summary", "s", "--validation", "v")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], cwd=self.sb, capture_output=True, text=True, encoding="utf-8")

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "core/src/guia.py", *args],
            cwd=self.sb, capture_output=True, text=True, encoding="utf-8",
        )

    def _ok(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = self._run(*args)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def test_refuses_without_reason_naming_each_lock(self) -> None:
        result = self._run("commit-message", "D-001")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("homologado", result.stderr)
        self.assertIn("adicoes", result.stderr)

    def test_message_passes_the_ci_lock_check(self) -> None:
        message = self._ok("commit-message", "D-001", "--unlock-reason", "pedido do teste").stdout
        self.assertTrue(message.startswith("🧹 chore(D-001): mexer em x"))
        self.assertIn("[unlock:homologado] motivo: pedido do teste", message)
        self.assertIn("[unlock:adicoes] motivo: pedido do teste", message)
        self.assertIn("Co-Authored-By: Agente <a@b>", message)
        (self.sb / "files.txt").write_text("M\tx.txt\nA\tnovo.txt\n", encoding="utf-8")
        (self.sb / "msg.txt").write_text(message, encoding="utf-8")
        check = subprocess.run(
            [sys.executable, "core/lock/check-lock.py", "ci", "--files", "files.txt", "--messages", "msg.txt"],
            cwd=self.sb, capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(check.returncode, 0, msg=check.stdout + check.stderr)

    def test_reason_per_lock_id(self) -> None:
        message = self._ok(
            "commit-message", "D-001",
            "--unlock-reason", "homologado=corrigir x",
            "--unlock-reason", "adicoes=arquivo novo pedido",
        ).stdout
        self.assertIn("[unlock:homologado] motivo: corrigir x", message)
        self.assertIn("[unlock:adicoes] motivo: arquivo novo pedido", message)


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class PrModeBranchFilesTests(unittest.TestCase):
    """D-137: no modo `pr` as marcas vem do que a branch muda (git), nao so do declarado.

    O squash leva a branch inteira; sem isso, um `ready` sem `--file` deixava a
    mensagem sem `[unlock:]` e o alwaysHuman (D-134) aprovava sozinho.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.sb = base / "app"
        (self.sb / "core" / "src").mkdir(parents=True)
        (self.sb / "core" / "lock").mkdir(parents=True)
        for src in CORE_SRC.glob("*.py"):
            if not src.name.startswith("__"):
                shutil.copy2(src, self.sb / "core" / "src" / src.name)
        shutil.copy2(CORE_LOCK / "lock_api.py", self.sb / "core" / "lock" / "lock_api.py")
        (self.sb / ".guia" / "locks").mkdir(parents=True)
        (self.sb / ".guia" / "locks" / "registry.yaml").write_text(REGISTRY, encoding="utf-8")
        (self.sb / ".guia" / "process.json").write_text(json.dumps({"delivery": {
            "mode": "pr", "commit": {"format": "gitmoji-conventional", "coAuthor": "Agente <a@b>"}}}), encoding="utf-8")
        (self.sb / ".gitignore").write_text(".guia/\ncore/\n", encoding="utf-8")
        (self.sb / "x.txt").write_text("x\n", encoding="utf-8")
        remote = base / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], capture_output=True)
        for args in (("init", "-q", "-b", "main"), ("config", "user.email", "t@t"), ("config", "user.name", "t"),
                     ("add", "."), ("commit", "-q", "-m", "seed"), ("remote", "add", "origin", str(remote)),
                     ("push", "-q", "-u", "origin", "main"), ("checkout", "-q", "-b", "d-001-mexer")):
            self.assertEqual(self._git(*args).returncode, 0, msg=str(args))
        result = self._run("chore", "mexer")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        (self.sb / "novo.txt").write_text("n\n", encoding="utf-8")
        self._git("add", "novo.txt")
        self._git("commit", "-q", "-m", "wip")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], cwd=self.sb, capture_output=True, text=True, encoding="utf-8")

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "core/src/guia.py", *args],
            cwd=self.sb, capture_output=True, text=True, encoding="utf-8",
        )

    def test_undeclared_new_file_on_the_branch_still_gets_the_mark(self) -> None:
        result = self._run("commit-message", "D-001", "--unlock-reason", "pedido do teste")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("[unlock:adicoes] motivo: pedido do teste", result.stdout)
        self.assertNotIn("homologado", result.stdout, "x.txt nao mudou na branch")

    def test_mark_without_reason_still_refuses(self) -> None:
        result = self._run("commit-message", "D-001")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("adicoes", result.stderr)


if __name__ == "__main__":
    unittest.main()
