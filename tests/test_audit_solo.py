"""D-193 (ADR-0021): no perfil SOLO o achado da auditoria volta para o agente.

`audit --approve` com `--finding` acima de `maxOpenFindings` e recusado: o
agente corrige na branch e audita o head novo - o dono nao e chamado. Dentro
do limite, aprova como sempre. Reusa o cenario da `test_audit` (PR real com
GitHub pelo fixture).
"""

from __future__ import annotations

import json
import unittest

import test_audit as base


class SoloAuditTests(unittest.TestCase):
    setUp = base.AuditTests.setUp
    tearDown = base.AuditTests.tearDown
    _run = base.AuditTests._run
    _ok = base.AuditTests._ok
    _comments = base.AuditTests._comments
    _task = base.AuditTests._task

    def _solo(self) -> None:
        process = self.main / ".guia" / "process.json"
        process.write_text(json.dumps({"delivery": {"mode": "pr"}, "autonomy": {"solo": "on"}}), encoding="utf-8")

    def test_solo_sends_open_findings_back_to_the_agent(self) -> None:
        self._solo()
        result = self._run(self.wt, "audit", "--report", str(self.report), "--approve", "--finding", "CORRIGIR=1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Corrija na branch", result.stderr)
        self.assertNotIn("audit", self._task())
        self.assertEqual(self._comments(), [])

    def test_solo_approves_when_findings_are_within_the_limit(self) -> None:
        self._solo()
        self._ok(self.wt, "audit", "--report", str(self.report), "--approve", "--finding", "CORRIGIR=0")
        self.assertEqual(self._task()["audit"]["result"], "approved")


if __name__ == "__main__":
    unittest.main()
