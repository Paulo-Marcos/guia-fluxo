"""D-097/ADR-0019: VERSION (raiz) e a fonte unica do numero de versao.

O renderer propaga o numero do VERSION para o campo `version` do plugin.json
e do marketplace.json, preservando o resto desses arquivos. Cobre:
- _sync_version_text reescreve so o campo version, preservando o entorno
- exige exatamente 1 campo "version" semver (0 ou 2+ aborta)
- _read_version le e valida o arquivo VERSION
- os 2 JSONs reais ficam em sincronia com o VERSION real (regressao do --check)
"""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

from conftest_paths import REPO_ROOT

RENDER = REPO_ROOT / "core" / "build" / "render-skills.py"


def _load_render_module(module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, RENDER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class VersionSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_render_module("render_probe_version_sync")

    def test_sync_rewrites_only_version_field(self) -> None:
        text = '{\n  "name": "guia",\n  "version": "0.4.0",\n  "license": "MIT"\n}\n'
        out = self.mod._sync_version_text(text, "1.2.3", Path("plugin.json"))
        self.assertIn('"version": "1.2.3"', out)
        # entorno preservado byte-a-byte (so o numero muda)
        self.assertEqual(out, text.replace("0.4.0", "1.2.3"))

    def test_sync_preserves_other_fields_via_json(self) -> None:
        text = '{\n  "version": "0.4.0",\n  "tags": ["a", "b"]\n}\n'
        out = self.mod._sync_version_text(text, "9.9.9", Path("x.json"))
        data = json.loads(out)
        self.assertEqual(data["version"], "9.9.9")
        self.assertEqual(data["tags"], ["a", "b"])

    def test_sync_aborts_without_version_field(self) -> None:
        with self.assertRaises(self.mod.RenderError):
            self.mod._sync_version_text('{"name": "x"}', "1.0.0", Path("x.json"))

    def test_sync_aborts_on_multiple_version_fields(self) -> None:
        text = '{"version": "0.1.0", "nested": {"version": "0.2.0"}}'
        with self.assertRaises(self.mod.RenderError):
            self.mod._sync_version_text(text, "1.0.0", Path("x.json"))

    def test_read_version_strips_and_validates(self) -> None:
        paths = self.mod.Paths.build(REPO_ROOT)
        version = self.mod._read_version(paths)
        self.assertRegex(version, r"^\d+\.\d+\.\d+")

    def test_real_jsons_in_sync_with_version_file(self) -> None:
        paths = self.mod.Paths.build(REPO_ROOT)
        version = self.mod._read_version(paths)
        for rel in self.mod.VERSION_SYNC_FILES:
            path = REPO_ROOT.joinpath(*rel)
            data = json.loads(path.read_text(encoding="utf-8"))
            found = data.get("version") or data["plugins"][0]["version"]
            self.assertEqual(
                found, version, msg=f"{'/'.join(rel)} fora de sincronia com VERSION"
            )


if __name__ == "__main__":
    unittest.main()
