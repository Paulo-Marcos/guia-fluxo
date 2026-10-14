"""D-150: no pilot, o lote de dependencias so para no dono no que vai alem de versao.

Arquivo por arquivo, pelo git: manifesto/lockfile modificado, workflow em que
toda linha mudada e `uses:` e o fragmento do proprio lote seguem sozinhos;
qualquer outro arquivo (codigo, linha de base, lockfile novo) ou trava tocada
para no dono com o motivo. Abaixo do pilot, o lockfile segue sendo alwaysHuman.
Lote de seguranca entra na fila como hotfix.
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

WORKFLOW = "on: push\njobs:\n  t:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n"
REGISTRY = """version: 1
locks:
- id: adicoes
  description: arquivo novo exige autorizacao
  operations: [add]
  files:
  - '*'
"""


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=", *args],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8",
    )


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class LotePilotTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.main = base / "app"
        (self.main / "core" / "src").mkdir(parents=True)
        (self.main / "core" / "lock").mkdir(parents=True)
        for src in CORE_SRC.glob("*.py"):
            if not src.name.startswith("__"):
                shutil.copy2(src, self.main / "core" / "src" / src.name)
        shutil.copy2(CORE_LOCK / "lock_api.py", self.main / "core" / "lock" / "lock_api.py")
        (self.main / ".guia" / "locks").mkdir(parents=True)
        (self.main / ".guia" / "locks" / "registry.yaml").write_text(REGISTRY, encoding="utf-8")
        self.process = {"delivery": {"mode": "pr"}, "autonomy": {"default": "pilot", "ceiling": "pilot"}}
        self._write_process()
        (self.main / ".gitignore").write_text(".guia/\ncore/\n", encoding="utf-8")
        (self.main / "requirements.txt").write_text("fastapi==0.110.0\n", encoding="utf-8")
        (self.main / "app.py").write_text("print('app')\n", encoding="utf-8")
        (self.main / ".github" / "workflows").mkdir(parents=True)
        (self.main / ".github" / "workflows" / "ci.yml").write_text(WORKFLOW, encoding="utf-8")
        self.remote = base / "remote.git"
        _git(base, "init", "-q", "--bare", str(self.remote))
        for args in (("init", "-q", "-b", "main"), ("add", "."), ("commit", "-q", "-m", "init"),
                     ("remote", "add", "origin", str(self.remote)), ("push", "-q", "-u", "origin", "main")):
            self.assertEqual(_git(self.main, *args).returncode, 0, msg=str(args))
        result = self._run("chore", "Atualizar as dependências do Dependabot em lote")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write_process(self) -> None:
        (self.main / ".guia" / "process.json").write_text(json.dumps(self.process), encoding="utf-8")

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, "core/src/guia.py", *args], cwd=self.main,
                              capture_output=True, text=True, encoding="utf-8")

    def _lote_pr(self, files: dict[str, str], security: bool = False) -> None:
        """Branch do lote no remoto com `files`, e a demanda como ship + audit gravariam."""
        task_id = json.loads((self.main / ".guia" / "tasks.json").read_text(encoding="utf-8"))["tasks"][0]["id"]
        _git(self.main, "checkout", "-q", "-b", "d-lote")
        for rel, content in files.items():
            path = self.main / rel.replace("{id}", task_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        _git(self.main, "add", "-A")
        _git(self.main, "commit", "-q", "-m", "lote")
        _git(self.main, "push", "-q", "origin", "d-lote")
        head = _git(self.main, "rev-parse", "HEAD").stdout.strip()
        _git(self.main, "checkout", "-q", "main")
        path = self.main / ".guia" / "tasks.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        task = data["tasks"][0]
        task.update(status="Em PR", dependabot={"prs": [11], "security": security})
        task["pr"] = {"number": 1, "url": "u", "branch": "d-lote", "head": head}
        task["audit"] = {"result": "approved", "auditedSha": head, "auditedPatchId": "p"}
        path.write_text(json.dumps(data), encoding="utf-8")
        (self.main / ".guia" / "queue").mkdir(exist_ok=True)
        (self.main / ".guia" / "queue" / f"{task_id}.msg").write_text(
            "x: lote\n\n[unlock:adicoes] motivo: fragmento\n", encoding="utf-8")
        result = self._run("queue", "add", task_id)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.out = result.stdout

    def _item(self) -> dict:
        return json.loads((self.main / ".guia" / "queue.json").read_text(encoding="utf-8"))["items"][0]

    def test_versions_only_go_alone_in_pilot(self) -> None:
        self._lote_pr({
            "requirements.txt": "fastapi==0.115.0\n",
            ".github/workflows/ci.yml": WORKFLOW.replace("@v4", "@v5"),
            "changelog.d/{id}.changed.md": "- deps (lote)\n",
        })
        self.assertEqual(self._item()["approval"]["by"], "autonomy", self.out)
        self.assertIsNone(self._item()["humanReason"])

    def test_code_change_stops_at_the_owner(self) -> None:
        self._lote_pr({"requirements.txt": "fastapi==0.115.0\n", "app.py": "print('mudou')\n"})
        self.assertIsNone(self._item()["approval"])
        self.assertIn("alem de versao: app.py", self._item()["humanReason"])

    def test_workflow_beyond_uses_stops(self) -> None:
        self._lote_pr({".github/workflows/ci.yml": WORKFLOW + "      - run: curl x | sh\n"})
        self.assertIn(".github/workflows/ci.yml", self._item()["humanReason"])

    def test_new_file_other_than_the_fragment_hits_the_lock(self) -> None:
        self._lote_pr({"requirements.txt": "fastapi==0.115.0\n", "package-lock.json": "{}\n"})
        reason = self._item()["humanReason"]
        self.assertIn("package-lock.json", reason, "lockfile novo e decisao")
        self.assertIn("toca trava: adicoes", reason)

    def test_below_pilot_lockfile_still_waits(self) -> None:
        self.process["autonomy"]["default"] = "queue"
        self._write_process()
        self._lote_pr({"requirements.txt": "fastapi==0.115.0\n"})
        self.assertIsNone(self._item()["approval"])
        self.assertIn("requirements.txt", self._item()["humanReason"])

    def test_security_lote_enters_as_hotfix(self) -> None:
        self._lote_pr({"requirements.txt": "fastapi==0.115.0\n"}, security=True)
        self.assertEqual(self._item()["priority"], "hotfix")


if __name__ == "__main__":
    unittest.main()
