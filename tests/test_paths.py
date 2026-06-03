"""Unit tests for core/src/_paths.py."""

from __future__ import annotations

import unittest
from pathlib import Path

from conftest_paths import REPO_ROOT, ensure_core_importable

ensure_core_importable()

import _paths  # noqa: E402


class NormalizePathTests(unittest.TestCase):
    def test_backslash_to_slash(self) -> None:
        self.assertEqual(_paths.normalize_path("src\\editor\\main.py"), "src/editor/main.py")

    def test_strip_leading_dotslash(self) -> None:
        self.assertEqual(_paths.normalize_path("./src"), "src")

    def test_trim_whitespace(self) -> None:
        self.assertEqual(_paths.normalize_path("  src/a  "), "src/a")


class SlugifyTests(unittest.TestCase):
    def test_lowercase_and_dash(self) -> None:
        self.assertEqual(_paths.slugify("Feature 015 - Refactor"), "feature-015-refactor")

    def test_strip_special_chars(self) -> None:
        self.assertEqual(_paths.slugify("hello, world!!"), "hello-world")

    def test_empty_returns_task(self) -> None:
        self.assertEqual(_paths.slugify("!!!"), "task")

    def test_max_length(self) -> None:
        long_value = "a" * 200
        self.assertEqual(len(_paths.slugify(long_value)), 80)


class RelativeTests(unittest.TestCase):
    def test_inside_repo(self) -> None:
        path = REPO_ROOT / "README.md"
        self.assertEqual(_paths.relative(path), "README.md")

    def test_outside_repo_fallback(self) -> None:
        outside = Path("/tmp/totally/outside")
        # nao explode; retorna posix string absoluta
        self.assertIsInstance(_paths.relative(outside), str)


if __name__ == "__main__":
    unittest.main()
