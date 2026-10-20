"""D-190: o aviso de plugin desatualizado nunca derruba o motor.

`status` e `doctor` leem os arquivos do Claude Code (`installed_plugins.json`,
`known_marketplaces.json`). Formato que o Claude Code mudar, ou arquivo
corrompido, vira silencio - nunca um traceback no `status`.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from conftest_paths import CORE_SRC

sys.path.insert(0, str(CORE_SRC))

from _plugin_version import stale_plugin_lines  # noqa: E402


class StalePluginTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.claude = Path(self._tmp.name)
        self.plugins = self.claude / "plugins"
        self.plugins.mkdir()
        patcher = mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(self.claude)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._tmp.cleanup)

    def _write(self, name: str, payload: object) -> None:
        (self.plugins / name).write_text(json.dumps(payload), encoding="utf-8")

    def test_missing_files_are_quiet(self) -> None:
        self.assertEqual(stale_plugin_lines(), [])

    def test_malformed_files_are_quiet(self) -> None:
        self._write("installed_plugins.json", {"plugins": {"guia@guia-fluxo": ["0.9.0", {"version": None}]}})
        self._write("known_marketplaces.json", ["nao e objeto"])
        self.assertEqual(stale_plugin_lines(), [])
        self._write("installed_plugins.json", [1, 2])
        self.assertEqual(stale_plugin_lines(), [])
        (self.plugins / "installed_plugins.json").write_text("{nao e json", encoding="utf-8")
        self.assertEqual(stale_plugin_lines(), [])

    def test_marketplace_with_odd_shapes_is_quiet(self) -> None:
        market = self.claude / "market"
        (market / ".claude-plugin").mkdir(parents=True)
        (market / ".claude-plugin" / "marketplace.json").write_text(
            json.dumps({"plugins": ["guia", {"name": "guia", "source": {"source": "github"}}]}), encoding="utf-8")
        self._write("known_marketplaces.json", {"guia-fluxo": {"source": "texto", "installLocation": str(market)}})
        self._write("installed_plugins.json", {"plugins": {"guia@guia-fluxo": [{"version": "0.9.0"}]}})
        self.assertEqual(stale_plugin_lines(), [])


if __name__ == "__main__":
    unittest.main()
