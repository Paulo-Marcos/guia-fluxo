"""D-132: a trava e a gravacao da fila toleram o PermissionError do Windows.

No Windows, um arquivo em "exclusao pendente" (outro processo acabou de
liberar a trava) devolve PermissionError no `os.open(O_EXCL)`, e o
`os.replace` falha enquanto outro processo le o arquivo. A fila esperava so
FileExistsError e o escritor caia. Pego de forma intermitente pelo teste das
20 escritas paralelas no CI Windows (PR #26). Aqui a falha e forcada uma vez,
de forma deterministica: o escritor tem de esperar e seguir.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from conftest_paths import ensure_core_importable

ensure_core_importable()

import _merge_queue  # noqa: E402


class WindowsPermissionErrorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        patches = [
            mock.patch.object(_merge_queue, "LOCK_FILE", base / "queue.lock"),
            mock.patch.object(_merge_queue, "QUEUE_FILE", base / "queue.json"),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_lock_retries_on_permission_error(self) -> None:
        real_open = os.open
        calls = {"n": 0}

        def flaky_open(path, flags, *args):
            calls["n"] += 1
            if calls["n"] == 1:
                raise PermissionError(13, "Permission denied", str(path))
            return real_open(path, flags, *args)

        with mock.patch("_merge_queue.os.open", side_effect=flaky_open):
            _merge_queue.mutate(lambda q: q["items"].append({"id": "X"}))
        self.assertEqual([i["id"] for i in _merge_queue.load()["items"]], ["X"])
        self.assertGreaterEqual(calls["n"], 2)

    def test_save_retries_on_permission_error(self) -> None:
        real_replace = os.replace
        calls = {"n": 0}

        def flaky_replace(src, dst):
            calls["n"] += 1
            if calls["n"] == 1:
                raise PermissionError(13, "Permission denied", str(dst))
            return real_replace(src, dst)

        with mock.patch("_merge_queue.os.replace", side_effect=flaky_replace):
            _merge_queue.mutate(lambda q: q["items"].append({"id": "Y"}))
        self.assertEqual([i["id"] for i in _merge_queue.load()["items"]], ["Y"])


if __name__ == "__main__":
    unittest.main()
