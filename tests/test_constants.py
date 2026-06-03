"""Sanity checks for the central constants module."""

from __future__ import annotations

import unittest

from conftest_paths import ensure_core_importable

ensure_core_importable()

import _constants  # noqa: E402


class StatusTagsTests(unittest.TestCase):
    def test_both_accented_and_plain_validacao_map(self) -> None:
        self.assertEqual(_constants.STATUS_TAGS["Aguardando validacao"], "VALIDACAO")
        self.assertEqual(_constants.STATUS_TAGS["Aguardando validação"], "VALIDACAO")


class PrefixTests(unittest.TestCase):
    def test_feature_and_issue_distinct(self) -> None:
        self.assertNotEqual(_constants.PREFIX_FEATURE, _constants.PREFIX_ISSUE)


class PathsTests(unittest.TestCase):
    def test_all_ai_paths_under_ai_dir(self) -> None:
        for path in (
            _constants.PROCESS_FILE,
            _constants.TASKS_FILE,
            _constants.BACKLOG_FILE,
            _constants.CURRENT_FILE,
            _constants.CHAT_TITLE_FILE,
            _constants.DOCS_MAP_FILE,
            _constants.REPORTS_DIR,
        ):
            self.assertEqual(path.parent, _constants.AI_DIR, f"{path} not under .ai/")


class MinPythonTests(unittest.TestCase):
    def test_min_python_is_3_10(self) -> None:
        self.assertEqual(_constants.MIN_PYTHON_MAJOR, 3)
        self.assertEqual(_constants.MIN_PYTHON_MINOR, 10)


if __name__ == "__main__":
    unittest.main()
