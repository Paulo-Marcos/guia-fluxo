"""F-018: tests for check-lock info / edit / history + --json on existing commands.

Cada caso roda check-lock contra um registry sandbox monkeypatched via
mocking de lock_api.REGISTRY/LOCK_IGNORE (mesmo padrao de test_lock_api).
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import REPO_ROOT, ensure_core_importable

ensure_core_importable()

import lock_api  # noqa: E402

CHECK_LOCK = REPO_ROOT / "core" / "lock" / "check-lock.py"


class _RegistrySandbox(unittest.TestCase):
    def setUp(self) -> None:
        self._original_registry = lock_api.REGISTRY
        self._original_lockignore = lock_api.LOCK_IGNORE
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        lock_api.REGISTRY = tmp / "registry.yaml"
        lock_api.LOCK_IGNORE = tmp / "lock-ignore.txt"
        lock_api.invalidate_caches()

    def tearDown(self) -> None:
        lock_api.REGISTRY = self._original_registry
        lock_api.LOCK_IGNORE = self._original_lockignore
        lock_api.invalidate_caches()
        self._tmp.cleanup()


class InfoTests(_RegistrySandbox):
    def test_info_returns_lock(self) -> None:
        spec = lock_api.LockSpec(id="t1", description="d", files=("a.txt",))
        lock_api.add_lock(spec, locked_at="2026-01-01", allow_missing=True)
        self.assertIsNotNone(lock_api.get_lock("t1"))
        self.assertIsNone(lock_api.get_lock("missing"))


class EditTests(_RegistrySandbox):
    def test_edit_adds_file(self) -> None:
        spec = lock_api.LockSpec(id="t1", files=("a.txt",))
        lock_api.add_lock(spec, locked_at="2026-01-01", allow_missing=True)
        updated = lock_api.edit_lock("t1", add_files=["b.txt"], allow_missing=True)
        self.assertIn("a.txt", updated["files"])
        self.assertIn("b.txt", updated["files"])

    def test_edit_removes_file(self) -> None:
        spec = lock_api.LockSpec(id="t1", files=("a.txt", "b.txt"))
        lock_api.add_lock(spec, locked_at="2026-01-01", allow_missing=True)
        updated = lock_api.edit_lock("t1", remove_files=["a.txt"])
        self.assertNotIn("a.txt", updated["files"])
        self.assertIn("b.txt", updated["files"])

    def test_edit_updates_description(self) -> None:
        spec = lock_api.LockSpec(id="t1", description="old", files=("a.txt",))
        lock_api.add_lock(spec, locked_at="2026-01-01", allow_missing=True)
        updated = lock_api.edit_lock("t1", description="new")
        self.assertEqual(updated["description"], "new")

    def test_edit_missing_raises(self) -> None:
        with self.assertRaises(lock_api.LockNotFound):
            lock_api.edit_lock("missing", add_files=["x.txt"], allow_missing=True)

    def test_edit_idempotent_add(self) -> None:
        """Re-adicionar mesmo arquivo nao duplica."""
        spec = lock_api.LockSpec(id="t1", files=("a.txt",))
        lock_api.add_lock(spec, locked_at="2026-01-01", allow_missing=True)
        updated = lock_api.edit_lock("t1", add_files=["a.txt"], allow_missing=True)
        self.assertEqual(updated["files"].count("a.txt"), 1)


class CheckLockJsonCLITests(unittest.TestCase):
    """Confirma que --json flag esta exposta nos subcomandos certos."""

    def test_list_json(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CHECK_LOCK), "list", "--json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("count", payload)
        self.assertIn("locks", payload)

    def test_check_json_unlocked(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CHECK_LOCK), "check", "--json", "README.md"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["blocked"], [])

    def test_audit_json_runs(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CHECK_LOCK), "audit", "--json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        # Pode ser 0 (com ou sem entries) - so verifica JSON parseavel
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("count", payload)
        self.assertIn("unlocks", payload)

    def test_history_json_with_existing_id(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CHECK_LOCK),
                "history",
                "--json",
                "adicoes-exigem-autorizacao",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["id"], "adicoes-exigem-autorizacao")
        self.assertIn("history", payload)

    def test_info_json_missing_returns_1(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CHECK_LOCK), "info", "--json", "nao-existe"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["found"])


if __name__ == "__main__":
    unittest.main()
