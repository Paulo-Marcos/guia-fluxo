"""D-079: tests for `guia backlog resolve`.

Cobre as duas fontes que `backlog list` une: tasks.json (D-NNN com
status=Backlog) e backlog.json legacy (B-NNN). Roda o CLI num sandbox
isolado para nao depender do estado do repo.
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


def _run(sandbox: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "core/src/guia.py", *args],
        cwd=sandbox,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _seed_legacy_backlog(sandbox: Path, item_id: str, title: str) -> None:
    """Escreve um item legacy em .guia/backlog.json (fixture de teste)."""
    backlog = sandbox / ".guia" / "backlog.json"
    payload = {
        "schemaVersion": 1,
        "items": [
            {"id": item_id, "title": title, "status": "Backlog", "context": title}
        ],
    }
    backlog.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _backlog_list_ids(sandbox: Path) -> list[str]:
    result = _run(sandbox, "backlog", "list")
    return [
        line.split()[0]
        for line in result.stdout.splitlines()
        if line and (line.startswith("D-") or line.startswith("B-"))
    ]


class BacklogResolveLegacyTests(unittest.TestCase):
    def test_resolve_legacy_item_drops_from_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            self.assertEqual(_run(sandbox, "init", "--project-name", "t").returncode, 0)
            _seed_legacy_backlog(sandbox, "B-009", "Item legacy entregue")
            self.assertIn("B-009", _backlog_list_ids(sandbox))

            result = _run(sandbox, "backlog", "resolve", "B-009", "--reason", "entregue em D-076")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertNotIn("B-009", _backlog_list_ids(sandbox))

            # Preservado no arquivo com status Resolvida + resolution.
            backlog = json.loads((sandbox / ".guia" / "backlog.json").read_text(encoding="utf-8"))
            entry = next(i for i in backlog["items"] if i["id"] == "B-009")
            self.assertEqual(entry["status"], "Resolvida")
            self.assertEqual(entry["resolution"], "entregue em D-076")
            self.assertIn("resolvedAt", entry)

    def test_resolve_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _seed_legacy_backlog(sandbox, "B-011", "Outro legacy")
            self.assertEqual(_run(sandbox, "backlog", "resolve", "B-011").returncode, 0)
            second = _run(sandbox, "backlog", "resolve", "B-011")
            self.assertEqual(second.returncode, 0)
            self.assertIn("ja esta resolvido", second.stdout)

    def test_resolve_missing_exits_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            result = _run(sandbox, "backlog", "resolve", "B-999")
            self.assertNotEqual(result.returncode, 0)


class BacklogResolveTasksTests(unittest.TestCase):
    def test_resolve_tasks_backlog_item(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            self.assertEqual(_run(sandbox, "init", "--project-name", "t").returncode, 0)
            # backlog add cria D-001 com status=Backlog em tasks.json.
            self.assertEqual(_run(sandbox, "backlog", "add", "Ideia parqueada").returncode, 0)
            self.assertIn("D-001", _backlog_list_ids(sandbox))

            result = _run(sandbox, "backlog", "resolve", "D-001", "--reason", "obsoleto")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertNotIn("D-001", _backlog_list_ids(sandbox))

            # Task preservada em tasks.json com status Resolvida.
            show = _run(sandbox, "tasks", "show", "D-001", "--json")
            self.assertEqual(show.returncode, 0, msg=show.stderr)
            task = json.loads(show.stdout)
            self.assertEqual(task["status"], "Resolvida")
            self.assertEqual(task["resolution"], "obsoleto")


if __name__ == "__main__":
    unittest.main()
