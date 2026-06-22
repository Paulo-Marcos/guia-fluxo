"""Unit tests for core/src/_tasks.py.

Os testes de geracao de IDs precisam isolar `_numbers_from_features`,
que le `FEATURES_FILE` do repo-mae. Monkeypatch direto na variavel do
modulo `_tasks` resolve.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from conftest_paths import ensure_core_importable

ensure_core_importable()

import _tasks  # noqa: E402
import _constants  # noqa: E402
from _constants import (  # noqa: E402
    KIND_FEATURE,
    KIND_ISSUE,
    STATUS_IN_DEVELOPMENT,
    STATUS_VALIDATED,
)


class NewTaskTests(unittest.TestCase):
    def test_default_shape(self) -> None:
        task = _tasks.new_task("F-001", KIND_FEATURE, "Title", "ctx", "origin")
        self.assertEqual(task["id"], "F-001")
        self.assertEqual(task["status"], STATUS_IN_DEVELOPMENT)
        self.assertEqual(task["kind"], KIND_FEATURE)
        self.assertIn(".guia/DEMANDAS.md", task["modifiedFiles"])

    def test_falls_back_context_to_title(self) -> None:
        task = _tasks.new_task("I-001", KIND_ISSUE, "MyTitle", "", "x")
        self.assertEqual(task["context"], "MyTitle")


class NextIdTests(unittest.TestCase):
    """Isolam FEATURES_FILE para nao colidir com os IDs reais do repo."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._original_features = _constants.FEATURES_FILE
        _tasks.FEATURES_FILE = Path(self._tmp.name) / "DEMANDAS.md"
        _constants.FEATURES_FILE = _tasks.FEATURES_FILE

    def tearDown(self) -> None:
        _tasks.FEATURES_FILE = self._original_features
        _constants.FEATURES_FILE = self._original_features
        self._tmp.cleanup()

    def test_next_id_zero(self) -> None:
        self.assertEqual(_tasks.next_task_id(KIND_FEATURE, []), "D-001")

    def test_next_id_after_existing(self) -> None:
        existing = [{"id": "F-001"}, {"id": "F-002"}, {"id": "I-001"}]
        self.assertEqual(_tasks.next_task_id(KIND_FEATURE, existing), "D-003")

    def test_next_id_monotonic_across_prefixes(self) -> None:
        # ADR-0011: IDs sao neutros (D-NNN) e o kind e ignorado. A
        # numeracao e monotonica considerando todos os prefixos vivos
        # (D/F/I), entao D-NNN nunca colide com um F-/I- ja existente.
        existing = [{"id": "F-007"}, {"id": "I-002"}]
        self.assertEqual(_tasks.next_task_id(KIND_ISSUE, existing), "D-008")


class MergeListTests(unittest.TestCase):
    def test_appends_new(self) -> None:
        task = {"summary": ["one"]}
        _tasks.merge_list(task, "summary", ["two", "three"])
        self.assertEqual(task["summary"], ["one", "two", "three"])

    def test_deduplicates(self) -> None:
        task = {"summary": ["one"]}
        _tasks.merge_list(task, "summary", ["one", "two"])
        self.assertEqual(task["summary"], ["one", "two"])

    def test_ignores_falsy(self) -> None:
        task = {"summary": []}
        _tasks.merge_list(task, "summary", ["", None, "valid"])
        self.assertEqual(task["summary"], ["valid"])


class StatusTagTests(unittest.TestCase):
    def test_known_status(self) -> None:
        self.assertEqual(_tasks.status_tag(STATUS_VALIDATED), "FINALIZADO")
        self.assertEqual(_tasks.status_tag(STATUS_IN_DEVELOPMENT), "DEV")

    def test_unknown_falls_back(self) -> None:
        self.assertEqual(_tasks.status_tag("Algum Status Custom"), "ALGUM_STATUS_CUSTOM")


if __name__ == "__main__":
    unittest.main()
