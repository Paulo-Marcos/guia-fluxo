"""D-091: tests for `guia upgrade` (migra layout antigo -> atual).

O comando deve detectar o layout pre-D-055/D-056 (FEATURES.md na raiz +
features/registry.yaml + features/lock-ignore.txt) e migrar para o atual
(.guia/DEMANDAS.md + .guia/locks/). Idempotente: NOOP quando ja atualizado.
"""

from __future__ import annotations

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


def _seed_old_layout(sandbox: Path) -> None:
    """Recria o layout pre-D-055/D-056 (FEATURES.md na raiz, features/ na raiz)."""
    (sandbox / "FEATURES.md").write_text("# Features e Issues\n\n", encoding="utf-8")
    features = sandbox / "features"
    features.mkdir()
    (features / "registry.yaml").write_text("version: 1\nlocks: []\n", encoding="utf-8")
    (features / "lock-ignore.txt").write_text(".gitignore\n", encoding="utf-8")


def _run(sandbox: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "core/src/guia.py", *args],
        cwd=sandbox,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


class UpgradeTests(unittest.TestCase):
    def test_noop_when_layout_is_current(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            result = _run(sandbox, "upgrade")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("ja esta atualizado", result.stdout)

    def test_dry_run_does_not_mutate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _seed_old_layout(sandbox)

            result = _run(sandbox, "upgrade", "--dry-run")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("Plano de migracao", result.stdout)
            self.assertIn("dry-run", result.stdout)

            # Layout antigo INTACTO.
            self.assertTrue((sandbox / "FEATURES.md").exists())
            self.assertTrue((sandbox / "features" / "registry.yaml").exists())
            self.assertFalse((sandbox / ".guia" / "DEMANDAS.md").exists())

    def test_migrates_old_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _seed_old_layout(sandbox)
            # Preserva conteudo distintivo p/ checar a migracao (nao copia+truncate).
            (sandbox / "FEATURES.md").write_text("ORIGINAL_DEMANDA\n", encoding="utf-8")
            (sandbox / "features" / "registry.yaml").write_text("ORIGINAL_REGISTRY\n", encoding="utf-8")

            result = _run(sandbox, "upgrade")
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            # Origem foi removida.
            self.assertFalse((sandbox / "FEATURES.md").exists())
            self.assertFalse((sandbox / "features" / "registry.yaml").exists())
            # Destino existe com o CONTEUDO original (move, nao recriacao).
            self.assertEqual(
                (sandbox / ".guia" / "DEMANDAS.md").read_text(encoding="utf-8"),
                "ORIGINAL_DEMANDA\n",
            )
            self.assertEqual(
                (sandbox / ".guia" / "locks" / "registry.yaml").read_text(encoding="utf-8"),
                "ORIGINAL_REGISTRY\n",
            )
            # features/ vazio foi removido.
            self.assertFalse((sandbox / "features").exists())

    def test_idempotent_after_migration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _seed_old_layout(sandbox)
            self.assertEqual(_run(sandbox, "upgrade").returncode, 0)
            # Rodar de novo = NOOP.
            second = _run(sandbox, "upgrade")
            self.assertEqual(second.returncode, 0, msg=second.stderr)
            self.assertIn("ja esta atualizado", second.stdout)

    def test_refuses_when_destination_exists(self) -> None:
        """Se o consumidor ja criou .guia/DEMANDAS.md (talvez por outra rota),
        upgrade nao deve sobrescrever - exige resolucao manual."""
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _seed_old_layout(sandbox)
            (sandbox / ".guia").mkdir(exist_ok=True)
            (sandbox / ".guia" / "DEMANDAS.md").write_text("ja existe\n", encoding="utf-8")

            result = _run(sandbox, "upgrade")
            self.assertEqual(result.returncode, 1, msg=result.stdout)
            self.assertIn("destino ja existe", result.stderr)
            # Origem preservada (nada foi mutado).
            self.assertTrue((sandbox / "FEATURES.md").exists())


if __name__ == "__main__":
    unittest.main()
