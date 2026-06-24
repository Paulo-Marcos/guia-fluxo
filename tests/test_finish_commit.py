"""D-081: finish/commit lida com arquivo deletado e e atomico com o status.

Dois defeitos que morderam no finish do D-077 (2026-06-20):

1. `git_commit` fazia `git add -- <files>`, que falha com "pathspec did not
   match any files" quando algum arquivo da task foi deletado -> commit aborta.
   Correcao: `git add -A -- <files>` stage adicoes, modificacoes E delecoes.

2. `cmd_finish` gravava status `Validada` (save_task) ANTES de commitar. Se o
   commit estourava, a task ficava persistida como Validada sem nenhum commit
   por tras -> estado inconsistente. Correcao: reverter o status no erro.

Os testes rodam o CLI real num sandbox temporario com um repo git de verdade.
Usam auto-init (primeira chamada de comando semeia `.guia/`) em vez de `guia
init`, evitando deploy do hook commit-msg e mantendo o commit livre de locks.
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

from conftest_paths import REPO_ROOT

CORE_SRC = REPO_ROOT / "core" / "src"
CORE_LOCK = REPO_ROOT / "core" / "lock"


def _seed(sandbox: Path) -> None:
    (sandbox / "core" / "src").mkdir(parents=True)
    (sandbox / "core" / "lock").mkdir(parents=True)
    for src in CORE_SRC.glob("*.py"):
        if not src.name.startswith("__"):
            shutil.copy2(src, sandbox / "core" / "src" / src.name)
    shutil.copy2(CORE_LOCK / "lock_api.py", sandbox / "core" / "lock" / "lock_api.py")


def _git(sandbox: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=sandbox,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _init_repo(sandbox: Path) -> None:
    _git(sandbox, "init")
    _git(sandbox, "config", "user.email", "test@example.com")
    _git(sandbox, "config", "user.name", "Test")
    _git(sandbox, "config", "commit.gpgsign", "false")


def _run(sandbox: Path, *args: str) -> subprocess.CompletedProcess[str]:
    # D-080: finish exige a env de autorizacao humana. A suite roda como o
    # desenvolvedor ja autorizado, entao a env fica setada para todo o CLI.
    env = {**os.environ, "GUIA_HUMAN_FINISH": "1"}
    return subprocess.run(
        [sys.executable, "core/src/guia.py", *args],
        cwd=sandbox,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )


def _show(sandbox: Path, task_id: str) -> dict:
    result = _run(sandbox, "tasks", "show", task_id, "--json")
    return json.loads(result.stdout)


def _head_files(sandbox: Path) -> list[str]:
    result = _git(sandbox, "ls-tree", "-r", "--name-only", "HEAD")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _commit_count(sandbox: Path) -> int:
    result = _git(sandbox, "rev-list", "--count", "HEAD")
    return int(result.stdout.strip() or "0")


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class FinishCommitDeletionTests(unittest.TestCase):
    def test_finish_commits_a_deleted_file(self) -> None:
        """Defeito 1: finish de uma task cujo arquivo foi deletado deve commitar
        a delecao em vez de abortar no `git add`."""
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _init_repo(sandbox)

            doomed = sandbox / "doomed.txt"
            doomed.write_text("conteudo\n", encoding="utf-8")
            _git(sandbox, "add", "doomed.txt")
            _git(sandbox, "commit", "-m", "seed: arquivo a deletar")
            before = _commit_count(sandbox)

            _run(sandbox, "chore", "Remove arquivo morto")
            doomed.unlink()

            result = _run(
                sandbox,
                "finish",
                "D-001",
                "--file",
                "doomed.txt",
                "--summary",
                "remove doomed.txt",
                "--validation",
                "n/a",
            )

            # (1) o commit acontece: returncode 0, novo commit, arquivo sumiu do HEAD.
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(_commit_count(sandbox), before + 1)
            self.assertNotIn("doomed.txt", _head_files(sandbox))
            self.assertEqual(_show(sandbox, "D-001")["status"], "Validada")


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class FinishCommitRollbackTests(unittest.TestCase):
    def test_status_not_validada_when_commit_fails(self) -> None:
        """Defeito 2: se o commit falha, o status NAO pode ficar `Validada`.

        Forca a falha deterministicamente: um arquivo nao relacionado fica
        staged, o que faz `commit_task` recusar (MSG_UNRELATED_STAGED) antes do
        commit. Sem rollback, a task ficaria Validada sem commit."""
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _init_repo(sandbox)

            tracked = sandbox / "tracked.txt"
            tracked.write_text("v1\n", encoding="utf-8")
            _git(sandbox, "add", "tracked.txt")
            _git(sandbox, "commit", "-m", "seed")
            before = _commit_count(sandbox)

            _run(sandbox, "chore", "Edita tracked")
            tracked.write_text("v2\n", encoding="utf-8")

            # Arquivo nao relacionado a task, mas staged -> commit_task recusa.
            intruder = sandbox / "intruder.txt"
            intruder.write_text("surpresa\n", encoding="utf-8")
            _git(sandbox, "add", "intruder.txt")

            result = _run(
                sandbox,
                "finish",
                "D-001",
                "--file",
                "tracked.txt",
                "--summary",
                "edita tracked",
                "--validation",
                "n/a",
            )

            # O finish falha e o status fica intacto (nao Validada); nada commitado.
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(_show(sandbox, "D-001")["status"], "Em desenvolvimento")
            self.assertEqual(_commit_count(sandbox), before)


if __name__ == "__main__":
    unittest.main()
