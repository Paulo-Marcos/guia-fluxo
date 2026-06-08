"""Unit tests for core/src/_features_md.py."""

from __future__ import annotations

import unittest

from conftest_paths import ensure_core_importable

ensure_core_importable()

import _features_md  # noqa: E402
from _constants import KIND_FEATURE, KIND_ISSUE  # noqa: E402


def _task(**overrides):
    base = {
        "id": "F-001",
        "kind": KIND_FEATURE,
        "title": "Some title",
        "status": "Em desenvolvimento",
        "origin": "Guia Fluxo (test)",
        "context": "Test ctx",
        "modifiedFiles": ["a.py", "b.py"],
        "summary": ["did A"],
        "validations": [],
        "pending": ["pending check"],
    }
    base.update(overrides)
    return base


class RenderBlockTests(unittest.TestCase):
    def test_includes_all_sections(self) -> None:
        rendered = _features_md.render_features_block(_task())
        self.assertIn("## [F-001] Some title", rendered)
        self.assertIn("### Arquivos modificados/criados", rendered)
        self.assertIn("### O que foi feito", rendered)
        self.assertIn("### Validacao feita", rendered)
        self.assertIn("### Validacao pendente", rendered)

    def test_empty_lists_print_nenhuma(self) -> None:
        rendered = _features_md.render_features_block(_task(validations=[], modifiedFiles=[]))
        self.assertIn("- Nenhuma.", rendered)

    def test_kind_label_feature_vs_issue(self) -> None:
        self.assertEqual(_features_md.task_kind_label(_task()), "Feature")
        self.assertEqual(
            _features_md.task_kind_label(_task(kind=KIND_ISSUE)),
            "Issue / regressao",
        )

    def test_markdown_list_wrap(self) -> None:
        result = _features_md.markdown_list(["a.py", "b.py"], "`")
        self.assertEqual(result, ["- `a.py`", "- `b.py`"])


if __name__ == "__main__":
    unittest.main()
