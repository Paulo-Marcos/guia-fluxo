"""D-123: `guia audit` - skill ou checklist embutido, comentario com o marcador (R4/R12).

Sem `--report`, so le: anuncia `skills.audit`, o head e o patch-id; com
`--skill-missing`, imprime o checklist embutido (portao nao vira aprovacao por
falta de skill). Com `--report`, comenta o relatorio no PR; com `--approve`,
fecha com o marcador do head e grava `auditedSha`/`auditedPatchId`. Recusa se
o head local nao e o que o remoto tem: o marcador tem de apontar o commit que
o GitHub ve.
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

from conftest_paths import CORE_LOCK, CORE_SRC, REPO_ROOT


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=", *args],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8",
    )


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class AuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.engine = base / "plugin" / "bin"
        self.engine.mkdir(parents=True)
        for src in CORE_SRC.glob("*.py"):
            if not src.name.startswith("__"):
                shutil.copy2(src, self.engine / src.name)
        shutil.copy2(CORE_LOCK / "lock_api.py", self.engine / "lock_api.py")
        shutil.copytree(REPO_ROOT / "core" / "templates", base / "plugin" / "templates")
        remote = base / "remote.git"
        self.main = base / "app"
        (self.main / ".guia").mkdir(parents=True)
        (self.main / ".guia" / "process.json").write_text(json.dumps({"delivery": {"mode": "pr"}}), encoding="utf-8")
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
        self.wt = base / "app-d001"
        (self.wt / "app.txt").write_text("app com nota\n", encoding="utf-8")
        _git(self.wt, "commit", "-q", "-am", "nota")
        self._ok(self.wt, "ready", "--file", "app.txt", "--request-test", "nota :: teste")
        self._ok(self.wt, "ship", "--body", "porque")
        self.report = base / "relatorio.md"
        self.report.write_text("## Auditoria\n\nRecomendação: mergear como está.\n", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.engine / "guia.py"), *args],
            cwd=cwd, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "GUIA_GH_FIXTURE": str(self.fixture), "CLAUDE_PLUGIN_ROOT": ""},
        )

    def _ok(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        result = self._run(cwd, *args)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def _comments(self) -> list[dict]:
        path = Path(str(self.fixture) + ".comments.json")
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []

    def _task(self) -> dict:
        return json.loads((self.main / ".guia" / "tasks.json").read_text(encoding="utf-8"))["tasks"][0]

    def _head(self) -> str:
        return _git(self.wt, "rev-parse", "HEAD").stdout.strip()

    def test_without_report_only_reads(self) -> None:
        result = self._ok(self.wt, "audit")
        self.assertIn("pr-audit", result.stderr)
        self.assertIn(self._head(), result.stdout)
        self.assertIn("patch-id", result.stdout)
        self.assertEqual(self._comments(), [])
        self.assertNotIn("audit", self._task())

    def test_missing_skill_prints_the_embedded_checklist(self) -> None:
        out = self._ok(self.wt, "audit", "--skill-missing", "pr-audit").stdout
        for piece in ("Fronteira de confiança", "Livro de alegações", "Portão hostil", "Pedido → Teste"):
            self.assertIn(piece, out)

    def test_approve_comments_the_marker_and_records_the_head(self) -> None:
        self._ok(self.wt, "audit", "--report", str(self.report), "--approve", "--skill-ran", "pr-audit")
        head = self._head()
        comment = self._comments()[0]
        self.assertEqual(comment["number"], self._task()["pr"]["number"])
        self.assertIn("Recomendação: mergear como está.", comment["body"])
        self.assertTrue(comment["body"].rstrip().endswith(f"<!-- auditoria-aprovada sha={head} -->"))
        audit = self._task()["audit"]
        self.assertEqual(audit["auditedSha"], head)
        self.assertTrue(audit["auditedPatchId"])
        self.assertEqual(audit["result"], "approved")
        runs = [(r["stage"], r["skill"], r["result"]) for r in self._task()["skillsRun"]]
        self.assertIn(("audit", "pr-audit", "ran"), runs)

    def test_report_without_approve_has_no_marker(self) -> None:
        self._ok(self.wt, "audit", "--report", str(self.report))
        self.assertNotIn("auditoria-aprovada", self._comments()[0]["body"])
        self.assertEqual(self._task()["audit"]["result"], "rejected")

    def test_refuses_when_head_is_not_on_the_remote(self) -> None:
        (self.wt / "app.txt").write_text("mais\n", encoding="utf-8")
        _git(self.wt, "commit", "-q", "-am", "depois do ship")
        result = self._run(self.wt, "audit", "--report", str(self.report), "--approve")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ship", result.stdout + result.stderr)
        self.assertEqual(self._comments(), [])

    def _rebase_with_change(self) -> tuple[str, str | None]:
        """A main anda; o autor faz rebase e muda algo (o patch-id nao bate). Devolve (H1, base1)."""
        audit = self._task()["audit"]
        (self.main / "outro.txt").write_text("outro\n", encoding="utf-8")
        _git(self.main, "add", "outro.txt")
        _git(self.main, "commit", "-q", "-m", "main andou")
        _git(self.main, "push", "-q", "origin", "main")
        _git(self.wt, "fetch", "-q", "origin")
        self.assertEqual(_git(self.wt, "rebase", "-q", "origin/main").returncode, 0)
        (self.wt / "app.txt").write_text("app com nota corrigida\n", encoding="utf-8")
        _git(self.wt, "commit", "-q", "-am", "ajuste no rebase")
        branch = _git(self.wt, "branch", "--show-current").stdout.strip()
        self.assertEqual(_git(self.wt, "push", "-q", "-f", "origin", branch).returncode, 0)
        return audit["auditedSha"], audit.get("auditedBase")

    def test_new_head_after_approval_is_audited_as_delta(self) -> None:
        """D-140 (R8): so o que mudou, pelo range-diff, e o registro diz de onde partiu."""
        self._ok(self.wt, "audit", "--report", str(self.report), "--approve")
        old_head, old_base = self._rebase_with_change()
        new_base = _git(self.wt, "merge-base", "HEAD", "origin/main").stdout.strip()
        expected = f"{old_base}..{old_head} {new_base}..{self._head()}"
        self.assertIn(f"git range-diff {expected}", self._ok(self.wt, "audit").stdout)
        self._ok(self.wt, "audit", "--report", str(self.report), "--approve")
        audit = self._task()["audit"]
        self.assertEqual((audit["mode"], audit["deltaFrom"], audit["range"]), ("delta", old_head, expected))
        self.assertEqual(audit["auditedBase"], new_base)
        self.assertTrue(self._comments()[-1]["body"].startswith(f"Auditoria de delta desde {old_head[:12]}"))

    def test_without_the_audited_base_the_audit_is_full(self) -> None:
        """Auditoria antiga sem `auditedBase`: diff inteiro, o lado seguro."""
        self._ok(self.wt, "audit", "--report", str(self.report), "--approve")
        self.assertEqual(self._task()["audit"]["mode"], "full")
        self._rebase_with_change()
        path = self.main / ".guia" / "tasks.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["tasks"][0]["audit"].pop("auditedBase")
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertNotIn("range-diff", self._ok(self.wt, "audit").stdout)
        self._ok(self.wt, "audit", "--report", str(self.report), "--approve")
        self.assertEqual(self._task()["audit"]["mode"], "full")

    def test_rejected_audit_never_becomes_a_delta_base(self) -> None:
        self._ok(self.wt, "audit", "--report", str(self.report))
        self._rebase_with_change()
        self.assertNotIn("range-diff", self._ok(self.wt, "audit").stdout)


if __name__ == "__main__":
    unittest.main()
