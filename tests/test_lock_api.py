"""Unit tests for core/lock/lock_api.py."""

from __future__ import annotations

import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from conftest_paths import ensure_core_importable

ensure_core_importable()

import lock_api  # noqa: E402


class _SandboxedLockApi(unittest.TestCase):
    """Reimporta lock_api apontando para um REPO_ROOT temporario.

    O modulo resolve REPO_ROOT em import-time (path absoluto na constante
    do modulo), entao o teste cria os arquivos features/ debaixo do
    repo-mae real e roda invalidate_caches() entre casos. As escritas
    sao em arquivos temporarios extra para nao bagunCar registry real
    do dogfood.
    """

    def setUp(self) -> None:
        self._original_registry = lock_api.REGISTRY
        self._original_lockignore = lock_api.LOCK_IGNORE
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        lock_api.REGISTRY = self.tmp / "registry.yaml"
        lock_api.LOCK_IGNORE = self.tmp / "lock-ignore.txt"
        lock_api.invalidate_caches()

    def tearDown(self) -> None:
        lock_api.REGISTRY = self._original_registry
        lock_api.LOCK_IGNORE = self._original_lockignore
        lock_api.invalidate_caches()
        self._tmp.cleanup()


class NormalizationTests(_SandboxedLockApi):
    def test_norm_path_handles_backslash(self) -> None:
        self.assertEqual(lock_api.norm_path("src\\editor\\main.py"), "src/editor/main.py")

    def test_norm_path_strips_leading_dotslash(self) -> None:
        self.assertEqual(lock_api.norm_path("./src/main.py"), "src/main.py")

    def test_matches_pattern_exact(self) -> None:
        self.assertTrue(lock_api.matches_pattern("src/a.py", "src/a.py"))

    def test_matches_pattern_glob(self) -> None:
        # fnmatch trata `*` como wildcard que cobre `/` tambem (comportamento padrao).
        # Para excluir subdiretorios, usar pattern mais estrito.
        self.assertTrue(lock_api.matches_pattern("src/*.py", "src/a.py"))
        self.assertTrue(lock_api.matches_pattern("**/*.md", "docs/x.md"))


class LockIgnoreTests(_SandboxedLockApi):
    def test_lock_ignore_loaded_and_cached(self) -> None:
        lock_api.LOCK_IGNORE.write_text(".gitignore\n# comment\n\n", encoding="utf-8")
        lock_api.invalidate_caches()
        self.assertEqual(lock_api.load_lock_ignore(), [".gitignore"])

    def test_lock_ignore_blocks_wildcard_lock(self) -> None:
        """Achado 5.Q4: lock-ignore deve vencer mesmo sob pattern `*`."""
        lock_api.LOCK_IGNORE.write_text(".gitignore\n", encoding="utf-8")
        lock_api.invalidate_caches()
        lock = {"id": "blanket", "files": ["*"], "operations": ["add"]}
        self.assertFalse(lock_api.lock_matches(lock, ".gitignore", "add"))
        # arquivo nao-ignorado continua bloqueado
        self.assertTrue(lock_api.lock_matches(lock, "src/new.py", "add"))


class UnlockedIdsTests(_SandboxedLockApi):
    def test_requires_motivo(self) -> None:
        """Achado 5.14: sem 'motivo:' o unlock nao vale."""
        self.assertEqual(lock_api.unlocked_ids("[unlock:foo]"), set())
        self.assertEqual(lock_api.unlocked_ids("[unlock:foo] motivo: justificativa"), {"foo"})

    def test_case_insensitive(self) -> None:
        self.assertEqual(
            lock_api.unlocked_ids("[UNLOCK:Foo] Motivo: bla"),
            {"foo"},
        )


class AddLockTests(_SandboxedLockApi):
    def test_add_then_load(self) -> None:
        # arquivo dummy precisa existir para nao precisar de --allow-missing
        target = self.tmp / "dummy.txt"
        target.write_text("x", encoding="utf-8")
        # add_lock checa contra REPO_ROOT real, entao usamos allow_missing
        spec = lock_api.LockSpec(
            id="t1",
            description="trava de teste",
            operations=("add",),
            files=("docs/auditorias/F-014-validacao.md",),
        )
        lock_api.add_lock(spec, locked_at="2026-01-01", allow_missing=True)
        locks = lock_api.load_locks()
        self.assertEqual(len(locks), 1)
        self.assertEqual(locks[0]["id"], "t1")
        self.assertEqual(locks[0]["operations"], ["add"])

    def test_duplicate_raises(self) -> None:
        spec = lock_api.LockSpec(id="dup", files=("a.txt",))
        lock_api.add_lock(spec, locked_at="2026-01-01", allow_missing=True)
        with self.assertRaises(lock_api.LockExists):
            lock_api.add_lock(spec, locked_at="2026-01-01", allow_missing=True)

    def test_path_traversal_blocked(self) -> None:
        """Achado 5.19: paths que escapam REPO_ROOT sao recusados."""
        spec = lock_api.LockSpec(id="evil", files=("../../../etc/passwd",))
        with self.assertRaises(lock_api.LockOutsideRepo):
            lock_api.add_lock(spec, locked_at="2026-01-01", allow_missing=True)


class EventsTests(_SandboxedLockApi):
    def test_events_from_name_status_rename(self) -> None:
        lines = ["R100\told.py\tnew.py"]
        events = lock_api.events_from_name_status(lines)
        paths = [(e.path, e.operation) for e in events]
        self.assertEqual(
            paths,
            [
                ("old.py", "rename"),
                ("old.py", "delete"),
                ("new.py", "rename"),
                ("new.py", "add"),
            ],
        )

    def test_events_from_paths_infer_modify_for_existing(self) -> None:
        # qualquer arquivo dentro deste repo sirvel
        existing = "README.md"
        events = lock_api.events_from_paths([existing])
        self.assertEqual(events[0].operation, "modify")


class ResolveRepoRootTests(unittest.TestCase):
    """_resolve_repo_root (D-076): GUIA_PROJECT_ROOT > script-se-tem-.guia > CWD.

    Faz o lock do consumidor plugin-global mirar o registry do projeto e
    nao o diretorio do plugin (uma copia de lock_api.py embarcada no plugin
    resolveria `parents[2]` para o dir do plugin sem este override)."""

    def test_env_override_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ):
            os.environ["GUIA_PROJECT_ROOT"] = tmp
            self.assertEqual(lock_api._resolve_repo_root(), Path(tmp).resolve())

    def test_without_env_uses_script_root_when_it_has_guia(self) -> None:
        # core/lock/lock_api.py -> parents[2] = repo-mae, que tem .guia/.
        with mock.patch.dict(os.environ):
            os.environ.pop("GUIA_PROJECT_ROOT", None)
            self.assertEqual(
                lock_api._resolve_repo_root(),
                Path(lock_api.__file__).resolve().parents[2],
            )


if __name__ == "__main__":
    unittest.main()
