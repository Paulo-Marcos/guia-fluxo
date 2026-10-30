"""D-203: so um painel do Guia conta como "ja aberto".

Outro servico local respondendo JSON na porta do painel nao pode fazer o
`painel` desistir de subir o servidor.
"""

from __future__ import annotations

import unittest
from unittest import mock

from conftest_paths import ensure_core_importable

ensure_core_importable()

import _cli_painel  # noqa: E402


def _response(body: bytes) -> mock.MagicMock:
    response = mock.MagicMock()
    response.__enter__.return_value.read.return_value = body
    return response


class ProbeTests(unittest.TestCase):
    def probe(self, body: bytes) -> str | None:
        with mock.patch.object(_cli_painel, "_PORT_TRIES", 1), \
                mock.patch.object(_cli_painel.urllib.request, "urlopen", return_value=_response(body)):
            return _cli_painel.running_dashboard(18998)

    def test_other_local_service_is_not_a_dashboard(self) -> None:
        self.assertIsNone(self.probe(b'{"status": "ok"}'))

    def test_guia_snapshot_is_a_dashboard(self) -> None:
        self.assertEqual(self.probe(b'{"projects": [], "guia": {}}'), "http://127.0.0.1:18998/")


if __name__ == "__main__":
    unittest.main()
