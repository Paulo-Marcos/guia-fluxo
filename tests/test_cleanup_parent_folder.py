"""D-202: worktrees e arquivos soltos poluem a pasta pai dos projetos.

Medido em 2026-10-29: `C:/DEV` tinha 31 pastas e 75 arquivos soltos. Cada
worktree nascia irma do repo (`../{repo}-{idCompact}`) e ficava la depois da
demanda integrada; agentes escreviam auditorias, logs de gate e mensagens na
raiz. Agora:

- o worktree nasce em `../{repo}-worktrees/{idCompact}` (uma pasta por projeto);
- `guia cleanup` lista worktrees inativas e arquivos soltos e so remove o que o
  dono escolher (`--remove`), nunca sozinho;
- `cleanup --session-start` e o relatorio de uma linha do hook SessionStart,
  mudo fora de um projeto Guia;
- artefatos de agente tem lugar fixo, `.guia/tmp/<D-NNN>/`, anunciado pelo `next`.
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


def _seed_engine_flat(bin_dir: Path) -> None:
    bin_dir.mkdir(parents=True)
    for src in CORE_SRC.glob("*.py"):
        if not src.name.startswith("__"):
            shutil.copy2(src, bin_dir / src.name)
    shutil.copy2(CORE_LOCK / "lock_api.py", bin_dir / "lock_api.py")


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=", *args],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8",
    )


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class CleanupParentFolderTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.engine = self.base / "plugin" / "bin"
        _seed_engine_flat(self.engine)
        self.dev = self.base / "dev"
        self.main = self.dev / "app"
        remote = self.base / "remote.git"
        (self.main / ".guia").mkdir(parents=True)
        (self.main / ".guia" / "process.json").write_text(
            json.dumps({"delivery": {"mode": "pr"}}), encoding="utf-8"
        )
        (self.main / ".gitignore").write_text(".guia/*\n!.guia/process.json\n", encoding="utf-8")
        (self.main / "app.txt").write_text("app\n", encoding="utf-8")
        _git(self.base, "init", "-q", "--bare", str(remote))
        for args in (("init", "-q", "-b", "main"), ("add", "."), ("commit", "-q", "-m", "init"),
                     ("remote", "add", "origin", str(remote)), ("push", "-q", "origin", "main")):
            self.assertEqual(_git(self.main, *args).returncode, 0, msg=str(args))
        self._ok("chore", "Primeira")
        self._ok("chore", "Segunda")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.engine / "guia.py"), *args],
            cwd=cwd or self.main, capture_output=True, text=True, encoding="utf-8",
        )

    def _ok(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        result = self._run(*args, cwd=cwd)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def _finished_worktree(self) -> Path:
        """D-001 com worktree e demanda encerrada (Cancelada e terminal)."""
        self._ok("worktree", "add", "D-001")
        self._ok("cancel", "D-001", "--reason", "teste", "--keep-worktree")
        return self.dev / "app-worktrees" / "d001"

    # 1. lugar proprio ---------------------------------------------------------

    def test_default_worktree_lives_in_the_project_worktrees_folder(self) -> None:
        self._ok("worktree", "add", "D-001")
        self.assertTrue((self.dev / "app-worktrees" / "d001").is_dir())
        self.assertFalse((self.dev / "app-d001").exists(), "nasceu irma do repo, na pasta pai")
        tasks = json.loads((self.main / ".guia" / "tasks.json").read_text(encoding="utf-8"))["tasks"]
        task = next(t for t in tasks if t["id"] == "D-001")
        self.assertEqual(task["worktree"]["path"], "../app-worktrees/d001")

    def test_worktree_in_the_old_layout_keeps_working(self) -> None:
        self._ok("worktree", "add", "D-001", "--path", "../app-d001")
        self.assertTrue((self.dev / "app-d001").is_dir())
        self._ok("worktree", "remove", "D-001")
        self.assertFalse((self.dev / "app-d001").exists())

    # 2. faxina ----------------------------------------------------------------

    def test_cleanup_lists_inactive_worktree_and_loose_files_without_removing(self) -> None:
        worktree = self._finished_worktree()
        self._ok("worktree", "add", "D-002")  # ativa: nao entra
        (self.dev / "auditoria-d001.md").write_text("x\n", encoding="utf-8")
        (self.dev / "gate-backend.log").write_text("x\n", encoding="utf-8")
        result = self._ok("cleanup", "--json")
        report = json.loads(result.stdout)
        paths = [Path(item["path"]).name for item in report["worktrees"]]
        self.assertEqual(paths, ["d001"])
        self.assertEqual(report["worktrees"][0]["task"], "D-001")
        files = sorted(Path(item["path"]).name for item in report["files"])
        self.assertEqual(files, ["auditoria-d001.md", "gate-backend.log"])
        self.assertTrue(worktree.is_dir(), "o relatorio nunca remove")
        self.assertTrue((self.dev / "gate-backend.log").exists())

    def test_cleanup_skips_inactive_worktree_with_local_changes(self) -> None:
        worktree = self._finished_worktree()
        (worktree / "app.txt").write_text("mudado\n", encoding="utf-8")
        report = json.loads(self._ok("cleanup", "--json").stdout)
        self.assertEqual(report["worktrees"], [])
        self.assertEqual([Path(item["path"]).name for item in report["kept"]], ["d001"])
        self.assertIn("mudanca", report["kept"][0]["why"])

    def test_cleanup_remove_takes_only_what_the_owner_chose(self) -> None:
        worktree = self._finished_worktree()
        (self.dev / "v1.txt").write_text("x\n", encoding="utf-8")
        (self.dev / "c982.msg").write_text("x\n", encoding="utf-8")
        self._ok("cleanup", "--remove", str(worktree), "--remove", "v1.txt")
        self.assertFalse(worktree.exists())
        self.assertFalse((self.dev / "v1.txt").exists())
        self.assertTrue((self.dev / "c982.msg").exists(), "nao escolhido: fica")
        self.assertTrue((self.dev / "app" / "app.txt").exists())

    def test_cleanup_remove_refuses_what_was_not_proposed(self) -> None:
        self._ok("worktree", "add", "D-002")
        active = self.dev / "app-worktrees" / "d002"
        result = self._run("cleanup", "--remove", str(active))
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(active.is_dir())
        self.assertTrue((self.main / "app.txt").exists())

    # 3. inicio de sessao -------------------------------------------------------

    def test_session_start_is_one_line_and_silent_when_clean(self) -> None:
        self.assertEqual(self._ok("cleanup", "--session-start").stdout.strip(), "")
        self._finished_worktree()
        (self.dev / "d968.patch").write_text("x\n", encoding="utf-8")
        out = self._ok("cleanup", "--session-start").stdout.strip()
        self.assertEqual(len(out.splitlines()), 1, out)
        self.assertIn("1 worktree", out)
        self.assertIn("1 arquivo", out)
        self.assertIn("cleanup", out)

    def test_session_start_outside_a_guia_project_is_silent_and_seeds_nothing(self) -> None:
        other = self.dev / "sem-guia"
        other.mkdir()
        result = self._run("cleanup", "--session-start", cwd=other)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")
        self.assertFalse((other / ".guia").exists())

    def test_old_worktree_without_record_is_found_by_branch_prefix(self) -> None:
        """Demandas antigas (gerador-cortes D-911) nao gravaram o worktree."""
        old = self.dev / "app-d001"
        self.assertEqual(_git(self.main, "worktree", "add", "-q", str(old), "-b", "d-001-antiga").returncode, 0)
        self._ok("cancel", "D-001", "--reason", "teste")
        report = json.loads(self._ok("cleanup", "--json").stdout)
        self.assertEqual([(Path(w["path"]).name, w["task"]) for w in report["worktrees"]], [("app-d001", "D-001")])
        self._ok("cleanup", "--remove", "D-001")
        self.assertFalse(old.exists())

    def test_app_worktrees_inside_the_repo_are_not_proposed(self) -> None:
        """`.claude/worktrees/` e do app: sessao viva com branch nova parece 'contida na base'."""
        inner = self.main / ".claude" / "worktrees" / "sessao-viva"
        self.assertEqual(_git(self.main, "worktree", "add", "-q", str(inner), "-b", "claude/sessao-viva").returncode, 0)
        report = json.loads(self._ok("cleanup", "--json").stdout)
        self.assertEqual(report["worktrees"] + report["kept"], [])

    def test_hook_entry_reports_without_loading_the_cli(self) -> None:
        (self.dev / "c982.msg").write_text("x\n", encoding="utf-8")
        hook = subprocess.run(
            [sys.executable, str(self.engine / "session_start.py")],
            cwd=self.main, capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(hook.returncode, 0, hook.stderr)
        self.assertIn("1 arquivo solto", hook.stdout)
        hooks = json.loads((CORE_SRC.parent / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        command = hooks["hooks"]["SessionStart"][0]["hooks"][0]["command"]
        self.assertIn("session_start.py", command)

    # 4. lugar fixo dos artefatos ----------------------------------------------

    def test_next_announces_the_artifacts_folder_inside_guia(self) -> None:
        step = json.loads(self._ok("next", "D-001", "--json").stdout)
        artifacts = Path(step["artifactsDir"])
        self.assertEqual(artifacts, (self.main / ".guia" / "tmp" / "D-001").resolve())
        self.assertTrue(artifacts.is_dir())
        self.assertEqual((self.main / ".guia" / "tmp" / ".gitignore").read_text(encoding="utf-8"), "*\n")


if __name__ == "__main__":
    unittest.main()
