"""D-175: o painel tem porta exclusiva - um segundo painel cai na proxima livre.

No Windows, o SO_REUSEADDR padrao do HTTPServer deixava dois processos na
mesma porta (medido na auditoria do PR #68).
"""

from __future__ import annotations

import unittest

from conftest_paths import ensure_core_importable

ensure_core_importable()

import _cli_dashboard  # noqa: E402


class ExclusivePortTests(unittest.TestCase):
    def test_second_dashboard_takes_the_next_port(self) -> None:
        first = _cli_dashboard._bind(18950)
        self.addCleanup(first.server_close)
        second = _cli_dashboard._bind(first.server_address[1])
        self.addCleanup(second.server_close)
        self.assertNotEqual(second.server_address[1], first.server_address[1])


if __name__ == "__main__":
    unittest.main()
