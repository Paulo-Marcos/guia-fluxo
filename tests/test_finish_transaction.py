"""D-111: finish no modo `pr` e finish como transacao unica (R1 + R10).

1. Modo `pr`: o codigo chega a main pelo squash do PR, entao o `finish` nao
   commita - nem com `finish.commitByDefault: true` no process.json - e
   `--commit` explicito e recusado.
2. D-579 (gerador-cortes): toda demanda nasce com `.guia/DEMANDAS.md` em
   `modifiedFiles`; com o arquivo no .gitignore, o `git add` abortava o
   commit do finish. Arquivo ignorado sai do pathspec.
3. Falha do commit desfaz a demanda inteira, nao so o status: o registro do
   portao (qualidade, resumo, arquivos) nao pode ficar gravado com o status
   antigo.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import CORE_LOCK, CORE_SRC


def _seed(sandbox: Path) -> None:
    (sandbox / "core" / "src").mkdir(parents=True)
    (sandbox / "core" / "lock").mkdir(parents=True)
    for src in CORE_SRC.glob("*.py"):
        if not src.name.startswith("__"):
            shutil.copy2(src, sandbox / "core" / "src" / src.name)
    shutil.copy2(CORE_LOCK / "lock_api.py", sandbox / "core" / "lock" / "lock_api.py")


def _git(sandbox: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
        cwd=sandbox,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _run(sandbox: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "core/src/guia.py", *args],
        cwd=sandbox,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _task(sandbox: Path, task_id: str) -> dict:
    tasks = json.loads((sandbox / ".guia" / "tasks.json").read_text(encoding="utf-8"))
    return next(t for t in tasks["tasks"] if t["id"] == task_id)


def _commit_count(sandbox: Path) -> int:
    return int(_git(sandbox, "rev-list", "--count", "HEAD").stdout.strip() or "0")


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class FinishTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.sandbox = Path(self._tmp.name)
        _seed(self.sandbox)
        _git(self.sandbox, "init", "-q")
        # Identidade na config do repo: o commit do motor nao recebe os `-c`
        # deste helper, e o runner do CI nao tem identidade global.
        _git(self.sandbox, "config", "user.email", "t@t")
        _git(self.sandbox, "config", "user.name", "t")
        _git(self.sandbox, "config", "commit.gpgsign", "false")
        (self.sandbox / "a.txt").write_text("a\n", encoding="utf-8")
        _git(self.sandbox, "add", "a.txt")
        _git(self.sandbox, "commit", "-q", "-m", "seed")
        created = _run(self.sandbox, "chore", "mudar a")
        self.assertEqual(created.returncode, 0, msg=created.stderr)
        (self.sandbox / "a.txt").write_text("a2\n", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _set_process(self, **changes: dict) -> None:
        path = self.sandbox / ".guia" / "process.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data.update(changes)
        path.write_text(json.dumps(data), encoding="utf-8")

    def _finish(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return _run(
            self.sandbox, "finish", "D-001", "--file", "a.txt",
            "--quality-skip", "teste", "--summary", "feito", *extra,
        )

    def test_pr_mode_does_not_commit_even_with_commit_by_default(self) -> None:
        self._set_process(delivery={"mode": "pr"}, finish={"commitByDefault": True})
        before = _commit_count(self.sandbox)
        result = self._finish()
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(_task(self.sandbox, "D-001")["status"], "Validada")
        self.assertEqual(_commit_count(self.sandbox), before)

    def test_pr_mode_refuses_explicit_commit(self) -> None:
        self._set_process(delivery={"mode": "pr"})
        result = self._finish("--commit")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("squash", result.stdout + result.stderr)
        self.assertEqual(_task(self.sandbox, "D-001")["status"], "Em desenvolvimento")

    def test_ignored_demandas_md_does_not_abort_commit(self) -> None:
        (self.sandbox / ".gitignore").write_text(".guia/\n", encoding="utf-8")
        before = _commit_count(self.sandbox)
        result = self._finish()
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertEqual(_commit_count(self.sandbox), before + 1)
        committed = _git(self.sandbox, "show", "--name-only", "--format=", "HEAD").stdout.split()
        self.assertEqual(committed, ["a.txt"])

    def test_failed_commit_rolls_back_the_whole_task(self) -> None:
        before = _task(self.sandbox, "D-001")
        hook = self.sandbox / ".git" / "hooks" / "commit-msg"
        hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        hook.chmod(0o755)
        result = self._finish()
        self.assertNotEqual(result.returncode, 0)
        after = _task(self.sandbox, "D-001")
        self.assertEqual(after["status"], before["status"])
        self.assertNotIn("qualityReview", after)
        self.assertEqual(after.get("summary"), before.get("summary"))
        self.assertEqual(after.get("modifiedFiles"), before.get("modifiedFiles"))


if __name__ == "__main__":
    unittest.main()
