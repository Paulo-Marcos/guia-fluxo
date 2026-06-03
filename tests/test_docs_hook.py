"""Unit tests for core/src/_docs_hook.py."""

from __future__ import annotations

import argparse
import unittest

from conftest_paths import ensure_core_importable

ensure_core_importable()

import _docs_hook  # noqa: E402
from _constants import KIND_FEATURE  # noqa: E402


def _task(**overrides):
    base = {
        "id": "F-099",
        "kind": KIND_FEATURE,
        "title": "T",
        "modifiedFiles": ["src/a.py"],
    }
    base.update(overrides)
    return base


def _docs_map(*entries):
    return {"docs": list(entries)}


class TriggerReasonTests(unittest.TestCase):
    def test_task_finished_always_matches(self) -> None:
        candidates = _docs_hook.compute_docs_candidates(
            _task(),
            ["src/a.py"],
            _docs_map({"path": "FEATURES.md", "triggers": [{"event": "task-finished"}]}),
        )
        self.assertEqual(len(candidates), 1)
        self.assertIn("task-finished: feature F-099", candidates[0]["reason"])

    def test_touched_matches_glob(self) -> None:
        candidates = _docs_hook.compute_docs_candidates(
            _task(),
            ["src/a.py"],
            _docs_map({
                "path": "docs/cli.md",
                "triggers": [{"event": "touched", "paths": ["src/*.py"]}],
            }),
        )
        self.assertEqual(len(candidates), 1)
        self.assertIn("touched: src/a.py", candidates[0]["reason"])

    def test_touched_no_match(self) -> None:
        candidates = _docs_hook.compute_docs_candidates(
            _task(modifiedFiles=["docs/x.md"]),
            [],
            _docs_map({
                "path": "FEATURES.md",
                "triggers": [{"event": "touched", "paths": ["src/*.py"]}],
            }),
        )
        self.assertEqual(candidates, [])

    def test_architectural_decision_always_matches(self) -> None:
        candidates = _docs_hook.compute_docs_candidates(
            _task(),
            [],
            _docs_map({"path": "adr/", "triggers": [{"event": "architectural-decision"}]}),
        )
        self.assertEqual(len(candidates), 1)

    def test_yaml_on_workaround_string_only(self) -> None:
        """trigger['on'] como string e aceito por compat (YAML 1.1 quebra `on:`)."""
        candidates = _docs_hook.compute_docs_candidates(
            _task(),
            [],
            _docs_map({"path": "x", "triggers": [{"on": "task-finished"}]}),
        )
        self.assertEqual(len(candidates), 1)

    def test_yaml_on_as_true_is_ignored(self) -> None:
        """trigger['on'] = True (bug do parser YAML 1.1) e silenciado."""
        candidates = _docs_hook.compute_docs_candidates(
            _task(),
            [],
            _docs_map({"path": "x", "triggers": [{"on": True}]}),
        )
        self.assertEqual(candidates, [])


class EnsureDocsReviewOkTests(unittest.TestCase):
    def _args(self, **kwargs):
        ns = argparse.Namespace(
            docs_touched=kwargs.get("docs_touched", []),
            docs_skip=kwargs.get("docs_skip", None),
            docs_checked=kwargs.get("docs_checked", False),
        )
        return ns

    def test_blocks_when_pending(self) -> None:
        with self.assertRaises(SystemExit):
            _docs_hook.ensure_docs_review_ok(
                _task(),
                [],
                _docs_map({"path": "x", "triggers": [{"event": "task-finished"}]}),
                self._args(),
            )

    def test_passes_when_touched(self) -> None:
        _docs_hook.ensure_docs_review_ok(
            _task(),
            [],
            _docs_map({"path": "x", "triggers": [{"event": "task-finished"}]}),
            self._args(docs_touched=["x"]),
        )

    def test_passes_when_skip(self) -> None:
        _docs_hook.ensure_docs_review_ok(
            _task(),
            [],
            _docs_map({"path": "x", "triggers": [{"event": "task-finished"}]}),
            self._args(docs_skip="motivo"),
        )

    def test_no_op_when_no_candidates(self) -> None:
        _docs_hook.ensure_docs_review_ok(_task(), [], _docs_map(), self._args())


if __name__ == "__main__":
    unittest.main()
