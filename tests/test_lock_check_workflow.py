"""D-168: o lock-check do CI so ve o que o PR muda, nao o que a main mudou depois.

Regressao: o passo "Collect changed files" fazia `git diff BASE_SHA HEAD_SHA`
(dois pontos). Com o PR atras da main, o que entrou na main depois da base do
PR aparecia invertido - teste criado na main virava "delete", teste editado
virava "modify" -, e a trava `testes-sao-contrato` barrava um PR que nao tocou
em teste nenhum (PR #53). O teste roda o `run:` do proprio workflow num repo
sandbox, para provar o comando que o CI executa, nao uma copia dele.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from conftest_paths import CORE_LOCK, REPO_ROOT

WORKFLOW = REPO_ROOT / ".github" / "workflows" / "lock-check.yml"
COLLECT_STEP = "Collect changed files and commit messages"
REGISTRY = """version: 1
locks:
- id: testes-sao-contrato
  description: Testes garantem o comportamento
  operations: [modify, delete, rename]
  files:
  - 'tests/*'
"""


def _bash() -> str | None:
    """O bash do Git no Windows (o `bash` do PATH pode ser o do WSL); no resto, o do PATH."""
    git = shutil.which("git")
    if os.name == "nt" and git:
        # git.exe vive em Git\cmd ou Git\mingw64\bin; o bash, em Git\bin.
        return next((str(parent / "bin" / "bash.exe") for parent in Path(git).parents
                     if (parent / "bin" / "bash.exe").is_file()), None)
    return shutil.which("bash")


BASH = _bash()


def _collect_script() -> str:
    jobs = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]
    steps = [step for job in jobs.values() for step in job.get("steps", [])]
    return next(step["run"] for step in steps if step.get("name") == COLLECT_STEP)


@unittest.skipUnless(shutil.which("git") and BASH, "git e bash (do Git) necessarios")
class LockCheckWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name) / "repo"
        self.out = Path(self._tmp.name) / "out"
        self.repo.mkdir()
        self.out.mkdir()
        self._git("init", "-q", "-b", "main")
        (self.repo / ".guia" / "locks").mkdir(parents=True)
        (self.repo / ".guia" / "locks" / "registry.yaml").write_text(REGISTRY, encoding="utf-8")
        (self.repo / "tests").mkdir()
        (self.repo / "tests" / "test_old.py").write_text("def test_old(): pass\n", encoding="utf-8")
        self._commit("base")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=", *args],
            cwd=self.repo, capture_output=True, text=True, encoding="utf-8", check=True,
        )
        return result.stdout.strip()

    def _commit(self, message: str) -> str:
        self._git("add", "-A")
        self._git("commit", "-q", "-m", message)
        return self._git("rev-parse", "HEAD")

    def _lock_check(self, base: str, head: str) -> subprocess.CompletedProcess[str]:
        """O passo de coleta do workflow + o check-lock ci, como no CI."""
        script = _collect_script().replace("/tmp/", self.out.as_posix() + "/")
        subprocess.run([BASH, "-c", script], cwd=self.repo, check=True, capture_output=True,
                       env={**os.environ, "BASE_SHA": base, "HEAD_SHA": head})
        return subprocess.run(
            [sys.executable, str(CORE_LOCK / "check-lock.py"), "ci",
             "--files", str(self.out / "files.txt"), "--messages", str(self.out / "messages.txt")],
            cwd=self.repo, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "GUIA_PROJECT_ROOT": str(self.repo)},
        )

    def test_behind_pr_is_not_blamed_for_test_changes_that_landed_on_main(self) -> None:
        self._git("checkout", "-q", "-b", "pr")
        (self.repo / "src.py").write_text("x = 1\n", encoding="utf-8")
        head = self._commit("feat: arquivo novo de producao")
        self._git("checkout", "-q", "main")
        (self.repo / "tests" / "test_old.py").write_text("def test_old(): assert True\n", encoding="utf-8")
        (self.repo / "tests" / "test_main_only.py").write_text("def test_m(): pass\n", encoding="utf-8")
        base = self._commit("main andou: [unlock:testes-sao-contrato] motivo: ja aprovado na main")

        result = self._lock_check(base, head)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        files = (self.out / "files.txt").read_text(encoding="utf-8")
        self.assertNotIn("tests/", files, "so o que o PR muda entra na conferencia")

    def test_pr_that_edits_a_locked_test_still_fails(self) -> None:
        self._git("checkout", "-q", "-b", "pr")
        (self.repo / "tests" / "test_old.py").write_text("def test_old(): assert False\n", encoding="utf-8")
        head = self._commit("feat: mexe no teste sem unlock")
        base = self._git("rev-parse", "main")

        result = self._lock_check(base, head)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("testes-sao-contrato", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
