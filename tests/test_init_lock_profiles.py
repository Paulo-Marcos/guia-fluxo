"""`init --locks <perfil>` escolhe qual registry de travas e deployado (D-158).

Perfis:
  - `adicoes` (default, retrocompativel): trava global de arquivo novo.
  - `testes`: trava modify/delete/rename nos testes existentes; arquivo novo
    (inclusive teste novo) e codigo de producao ficam livres.
  - `nenhum`: registry vazio + hook instalados (travas podem vir depois).
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core" / "lock"))

import yaml  # noqa: E402
from test_init_deploy import (  # noqa: E402
    HOOK_SRC,
    TEMPLATES_SRC,
    _git_init,
    _run_init,
    _seed_engine_flat,
)

import lock_api  # noqa: E402


def _seed_all_templates(plugin_root: Path) -> None:
    locks = plugin_root / "templates" / "locks"
    locks.mkdir(parents=True)
    for src in (TEMPLATES_SRC / "locks").iterdir():
        shutil.copy2(src, locks / src.name)
    githooks = plugin_root / "templates" / ".githooks"
    githooks.mkdir(parents=True)
    shutil.copy2(HOOK_SRC, githooks / "commit-msg")


class InitLockProfilesTest(unittest.TestCase):
    def _init(self, *extra: str):
        cache_tmp = tempfile.TemporaryDirectory()
        project_tmp = tempfile.TemporaryDirectory()
        self.addCleanup(cache_tmp.cleanup)
        self.addCleanup(project_tmp.cleanup)
        plugin_root = Path(cache_tmp.name) / "plugin"
        _seed_engine_flat(plugin_root / "bin")
        _seed_all_templates(plugin_root)
        project = Path(project_tmp.name)
        _git_init(project)
        return _run_init(plugin_root, project, *extra), project

    def _locks(self, project: Path) -> list[dict]:
        registry = project / ".guia" / "locks" / "registry.yaml"
        return yaml.safe_load(registry.read_text(encoding="utf-8"))["locks"] or []

    def test_default_profile_keeps_global_add_lock(self) -> None:
        result, project = self._init()
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual([lock["id"] for lock in self._locks(project)], ["adicoes-exigem-autorizacao"])

    def test_testes_profile_locks_existing_tests_only(self) -> None:
        result, project = self._init("--locks", "testes")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue((project / ".githooks" / "commit-msg").is_file())
        locks = self._locks(project)
        self.assertEqual([lock["id"] for lock in locks], ["testes-sao-contrato"])
        lock = locks[0]

        def blocked(path: str, op: str) -> bool:
            return op in lock_api.lock_operations(lock) and any(
                lock_api.matches_pattern(p, path) for p in lock["files"]
            )

        for path in (
            "tests/test_calc.py",
            "tests/unit/test_calc.py",
            "src/app/tests/test_x.py",
            "web/src/__tests__/Button.tsx",
            "web/src/Button.test.tsx",
            "web/src/Button.spec.ts",
            "src/MyApp.Tests/CalcTests.cs",
            "pkg/calc_test.go",
        ):
            self.assertTrue(blocked(path, "modify"), msg=f"deveria travar {path}")
            self.assertTrue(blocked(path, "delete"), msg=f"deveria travar delete {path}")
            self.assertFalse(blocked(path, "add"), msg=f"teste novo deve ser livre: {path}")

        for path in ("src/calc.py", "src/latest_news.py", "web/src/Button.tsx", "src/MyApp/Calc.cs"):
            self.assertFalse(blocked(path, "modify"), msg=f"producao deve ser livre: {path}")

    def test_nenhum_profile_deploys_empty_registry_and_hook(self) -> None:
        result, project = self._init("--locks", "nenhum")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(self._locks(project), [])
        self.assertTrue((project / ".githooks" / "commit-msg").is_file())

    def test_unknown_profile_is_rejected(self) -> None:
        result, _project = self._init("--locks", "tudo")
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
