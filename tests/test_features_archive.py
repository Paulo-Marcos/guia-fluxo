"""Unit tests for core/src/_features_archive.py (D-090).

Keeps only the N newest demand blocks in .guia/DEMANDAS.md and moves older
ones to .guia/historico/ with the ai-skip marker. Isolates the module-level
paths into a tmp dir so the real repo state is untouched.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from conftest_paths import ensure_core_importable

ensure_core_importable()

import _features_archive  # noqa: E402
import _features_md  # noqa: E402
from _constants import ARCHIVE_HEADER, ARCHIVE_MARKER, FEATURES_HEADER, KIND_FEATURE  # noqa: E402


def _task(num: int):
    return {
        "id": f"D-{num:03d}",
        "kind": KIND_FEATURE,
        "title": f"Title {num}",
        "status": "Em desenvolvimento",
        "origin": "Guia Fluxo (test)",
        "context": f"ctx {num}",
        "modifiedFiles": ["a.py"],
        "summary": [f"did {num}"],
        "validations": [],
        "pending": [],
    }


class ArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self._features = root / "DEMANDAS.md"
        self._archive = root / "historico" / "DEMANDAS.md"
        self._process = root / "process.json"

        # Snapshot + redirect every module-level path the two modules touch.
        self._orig = {
            (_features_md, "FEATURES_FILE"): _features_md.FEATURES_FILE,
            (_features_archive, "FEATURES_FILE"): _features_archive.FEATURES_FILE,
            (_features_archive, "ARCHIVE_FILE"): _features_archive.ARCHIVE_FILE,
            (_features_archive, "PROCESS_FILE"): _features_archive.PROCESS_FILE,
        }
        _features_md.FEATURES_FILE = self._features
        _features_archive.FEATURES_FILE = self._features
        _features_archive.ARCHIVE_FILE = self._archive
        _features_archive.PROCESS_FILE = self._process

    def tearDown(self) -> None:
        for (mod, attr), value in self._orig.items():
            setattr(mod, attr, value)
        self._tmp.cleanup()

    def _set_keep(self, keep: int) -> None:
        self._process.write_text(
            json.dumps({"archive": {"keepInDemandas": keep}}),
            encoding="utf-8",
        )

    def _ids_in(self, path: Path) -> list[str]:
        text = path.read_text(encoding="utf-8")
        return _features_archive._HEADING_ID_RE.findall(text)

    def test_keeps_n_archives_the_rest(self) -> None:
        keep = 5
        self._set_keep(keep)
        # N+5 demandas. upsert insere a mais nova no topo e arquiva a cada vez.
        for num in range(1, keep + 6):
            _features_md.upsert_features_entry(_task(num))

        kept = self._ids_in(self._features)
        self.assertEqual(len(kept), keep)
        # As 5 mais novas ficam; as 5 mais antigas saem.
        self.assertEqual(set(kept), {f"D-{n:03d}" for n in range(6, 11)})

        archived = self._ids_in(self._archive)
        self.assertEqual(set(archived), {f"D-{n:03d}" for n in range(1, 6)})

        # Marcador ai-skip no TOPO do historico (agente checa antes de carregar).
        history = self._archive.read_text(encoding="utf-8")
        self.assertTrue(history.startswith(ARCHIVE_MARKER))
        self.assertIn("archive=true", history)
        self.assertIn("ai-skip=true", history)

        # Nenhum ID arquivado vaza de volta para o DEMANDAS.md.
        self.assertFalse(set(kept) & set(archived))

    def test_noop_below_threshold(self) -> None:
        self._features.write_text(FEATURES_HEADER, encoding="utf-8")
        for num in range(1, 4):
            _features_md.upsert_features_entry(_task(num))
        self._set_keep(30)
        _features_archive.archive_old_entries()
        self.assertEqual(len(self._ids_in(self._features)), 3)
        self.assertFalse(self._archive.exists())

    def test_idempotent(self) -> None:
        keep = 3
        self._set_keep(keep)
        for num in range(1, keep + 4):  # keep + 3 extras
            _features_md.upsert_features_entry(_task(num))

        first_main = self._features.read_text(encoding="utf-8")
        first_hist = self._archive.read_text(encoding="utf-8")

        # Rodar de novo nao duplica nem corrompe.
        _features_archive.archive_old_entries()
        _features_archive.archive_old_entries()

        self.assertEqual(self._features.read_text(encoding="utf-8"), first_main)
        self.assertEqual(self._archive.read_text(encoding="utf-8"), first_hist)
        # Sem IDs duplicados no historico.
        archived = self._ids_in(self._archive)
        self.assertEqual(len(archived), len(set(archived)))

    def test_keep_zero_archives_all(self) -> None:
        self._features.write_text(FEATURES_HEADER, encoding="utf-8")
        for num in range(1, 4):
            _features_md.upsert_features_entry(_task(num))
        _features_archive.archive_old_entries(keep=0)
        self.assertEqual(self._ids_in(self._features), [])
        self.assertEqual(len(self._ids_in(self._archive)), 3)


if __name__ == "__main__":
    unittest.main()
