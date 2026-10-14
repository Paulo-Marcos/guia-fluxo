"""D-161: a etapa `locks-profile` do configurador grava o registry de travas.

Decisao do Paulo: e a excecao ao "o configure so grava o process.json" (D-143).
O perfil (os mesmos do `init --locks`, D-158) e detectado pelos ids das travas
do registry atual; `--set locks-profile=<perfil> --yes` troca o registry pelo
template, com backup em .guia/backups/, e nao escreve nada no process.json.
Registry personalizado (travas fora dos perfis) e mantido por recomendacao.
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

import yaml

from conftest_paths import CORE_LOCK, CORE_SRC

CORE_TEMPLATES = CORE_SRC.parent / "templates"


class ConfigureLocksTests(unittest.TestCase):
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
        shutil.copytree(CORE_TEMPLATES / "locks", self.main / "core" / "templates" / "locks")
        (self.main / ".guia").mkdir()
        self.process = self.main / ".guia" / "process.json"
        self.process.write_text(json.dumps({"projectName": "app"}), encoding="utf-8")
        self.registry = self.main / ".guia" / "locks" / "registry.yaml"
        subprocess.run(["git", "init", "-q"], cwd=self.main, check=True, capture_output=True)
        self.fixture = base / "gh.json"
        self.fixture.write_text(json.dumps({"__auth__": True}), encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "core/src/guia.py", "configure", *args],
            cwd=self.main, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "GUIA_GH_FIXTURE": str(self.fixture)},
        )

    def _ok(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = self._run(*args)
        self.assertEqual(result.returncode, 0, msg=f"{args}: {result.stdout}{result.stderr}")
        return result

    def _step(self) -> dict:
        steps = json.loads(self._ok("--plan", "--json").stdout)["steps"]
        return next(step for step in steps if step["id"] == "locks-profile")

    def _write_registry(self, template: str) -> None:
        self.registry.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(CORE_TEMPLATES / "locks" / template, self.registry)

    def _lock_ids(self) -> list[str]:
        data = yaml.safe_load(self.registry.read_text(encoding="utf-8")) or {}
        return [lock["id"] for lock in data.get("locks") or []]

    def test_without_registry_recommends_testes(self) -> None:
        step = self._step()
        self.assertTrue(step["applies"])
        self.assertIsNone(step["current"])
        self.assertEqual(step["recommended"], "testes")
        self.assertEqual(step["status"], "nova")
        self.assertEqual({o["value"] for o in step["options"]}, {"adicoes", "testes", "nenhum"})

    def test_detects_the_current_profile(self) -> None:
        self._write_registry("registry.yaml")
        step = self._step()
        self.assertEqual(step["current"], "adicoes")
        self.assertEqual(step["status"], "difere")

    def test_custom_registry_is_kept_by_recommendation(self) -> None:
        self._write_registry("registry.testes.yaml")
        with self.registry.open("a", encoding="utf-8") as handle:
            handle.write("- id: homologado\n  files: [src/core.py]\n")
        step = self._step()
        self.assertEqual(step["current"], "personalizado")
        self.assertEqual(step["recommended"], "personalizado")
        self.assertEqual(step["status"], "ok")

    def test_set_without_yes_only_simulates(self) -> None:
        self._write_registry("registry.yaml")
        out = self._ok("--set", "locks-profile=testes").stdout
        self.assertIn(".guia/locks/registry.yaml", out)
        self.assertIn("Simulacao", out)
        self.assertEqual(self._lock_ids(), ["adicoes-exigem-autorizacao"])

    def test_yes_writes_registry_with_backup_and_leaves_process_json(self) -> None:
        self._write_registry("registry.yaml")
        before = self.registry.read_text(encoding="utf-8")
        process_before = self.process.read_text(encoding="utf-8")
        result = json.loads(self._ok("--set", "locks-profile=testes", "--yes", "--json").stdout)
        self.assertTrue(result["written"])
        self.assertEqual(self._lock_ids(), ["testes-sao-contrato"])
        backups = list((self.main / ".guia" / "backups").glob("registry.yaml.*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(encoding="utf-8"), before)
        self.assertEqual(self.process.read_text(encoding="utf-8"), process_before, "process.json nao muda")

    def test_creates_registry_when_absent(self) -> None:
        self._ok("--set", "locks-profile=nenhum", "--yes")
        self.assertEqual(self._lock_ids(), [])
        self.assertFalse((self.main / ".guia" / "backups").exists(), "sem registry anterior, sem backup")

    def test_bad_profile_is_refused(self) -> None:
        self.assertIn("nao e uma opcao", self._run("--set", "locks-profile=tudo").stderr)
        self.assertIn("nao e uma opcao", self._run("--set", "locks-profile=personalizado").stderr)


if __name__ == "__main__":
    unittest.main()
