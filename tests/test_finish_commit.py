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
    return subprocess.run(
        [sys.executable, "core/src/guia.py", *args],
        cwd=sandbox,
        capture_output=True,
        text=True,
        encoding="utf-8",
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
                # D-095: arquivo de produto mudou -> gate de qualidade exige
                # confirmacao; aqui validamos para testar o commit em si.
                "--quality-checked",
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

        Forca a falha deterministicamente com um hook `commit-msg` que rejeita
        (exit 1), fazendo `git commit` estourar. Sem rollback, a task ficaria
        Validada sem commit por tras. (Ate o D-105 este teste forcava a falha
        com um arquivo alheio staged - hoje isso NAO falha mais: o commit por
        pathspec ignora o index alheio; ver test_finish_isolates_*.)"""
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

            # commit-msg que rejeita qualquer commit -> git commit retorna != 0.
            hook = sandbox / ".git" / "hooks" / "commit-msg"
            hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            hook.chmod(0o755)

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
                # D-095: passa o gate de qualidade para exercitar o rollback do
                # commit (o ponto deste teste), nao parar antes no gate.
                "--quality-checked",
            )

            # O finish falha e o status fica intacto (nao Validada); nada commitado.
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(_show(sandbox, "D-001")["status"], "Em desenvolvimento")
            self.assertEqual(_commit_count(sandbox), before)


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class FinishCommitIsolationTests(unittest.TestCase):
    """D-105: o commit de encerramento so pode selar os arquivos DESTA demanda,
    mesmo com outra demanda (outro chat/agente em paralelo) com arquivos ja
    staged na mesma arvore. Antes, o `git commit` sem pathspec engolia o index
    inteiro; agora commita por pathspec."""

    def test_finish_isolates_concurrent_staged_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _init_repo(sandbox)

            tracked = sandbox / "tracked.txt"
            tracked.write_text("v1\n", encoding="utf-8")
            _git(sandbox, "add", "tracked.txt")
            _git(sandbox, "commit", "-m", "seed")

            _run(sandbox, "chore", "Edita tracked")
            tracked.write_text("v2\n", encoding="utf-8")

            # Simula outra demanda em paralelo: um arquivo dela ja esta staged.
            intruder = sandbox / "intruder.txt"
            intruder.write_text("trabalho de outra demanda\n", encoding="utf-8")
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
                "--quality-checked",
            )

            # O finish fecha com sucesso, commita tracked.txt e NAO engole o
            # intruder.txt (fica de fora do HEAD, intacto no working tree).
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            head = _head_files(sandbox)
            self.assertIn("tracked.txt", head)
            self.assertNotIn("intruder.txt", head)
            self.assertTrue(intruder.exists())
            self.assertEqual(_show(sandbox, "D-001")["status"], "Validada")


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class FinishRequiresDeclaredFilesTests(unittest.TestCase):
    """D-105: com commit, o finish recusa quando nenhum arquivo de produto foi
    declarado (nem via --file, nem acumulado num ready). O motor nao infere da
    arvore inteira, entao exige a declaracao para nao commitar so o bookkeeping
    e deixar o codigo de fora."""

    def test_finish_refuses_commit_without_declared_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _init_repo(sandbox)

            seed = sandbox / "seed.txt"
            seed.write_text("x\n", encoding="utf-8")
            _git(sandbox, "add", "seed.txt")
            _git(sandbox, "commit", "-m", "seed")
            before = _commit_count(sandbox)

            _run(sandbox, "chore", "Mexe em codigo mas esquece --file")
            # Ha trabalho de produto na arvore, mas o agente nao o declarou.
            feature = sandbox / "feature.txt"
            feature.write_text("codigo novo\n", encoding="utf-8")

            result = _run(
                sandbox,
                "finish",
                "D-001",
                "--summary",
                "fecha sem declarar arquivos",
                "--quality-skip",
                "n/a",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--file", result.stderr)
            self.assertEqual(_show(sandbox, "D-001")["status"], "Em desenvolvimento")
            self.assertEqual(_commit_count(sandbox), before)

    def test_finish_no_commit_allowed_without_files(self) -> None:
        """Contraparte: --no-commit nao commita, entao nao exige --file."""
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _init_repo(sandbox)
            _git(sandbox, "commit", "--allow-empty", "-m", "seed")

            _run(sandbox, "chore", "Fecha sem commit")
            result = _run(
                sandbox,
                "finish",
                "D-001",
                "--no-commit",
                "--summary",
                "dry close",
                "--quality-skip",
                "n/a",
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(_show(sandbox, "D-001")["status"], "Validada")


if __name__ == "__main__":
    unittest.main()
