"""D-052: timing rico + stats de throughput.

Duas frentes:

1. Unidade (rapida, sem subprocess) sobre `_stats.compute_stats`: a
   matematica de elapsed/active e o backfill = null para tasks legadas.
2. Integracao (subprocess da CLI num sandbox) do ciclo completo
   create -> block -> unblock -> ready -> finish, congelando o relogio via
   a env `GUIA_NOW` por chamada e conferindo os numeros via `stats --json`.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import REPO_ROOT, ensure_core_importable

ensure_core_importable()

import _stats  # noqa: E402

CORE_SRC = REPO_ROOT / "core" / "src"
LOCK_API = REPO_ROOT / "core" / "lock" / "lock_api.py"


# --- Timeline congelada usada pelo teste de integracao (offset ISO-8601) ---
T_START = "2026-06-01T10:00:00+00:00"
T_BLOCK = "2026-06-01T10:00:30+00:00"
T_UNBLOCK = "2026-06-01T10:01:30+00:00"  # bloqueado por 60s
T_READY = "2026-06-01T10:02:00+00:00"
T_FINISH = "2026-06-01T10:05:00+00:00"  # 300s total desde o start


class ComputeStatsUnitTests(unittest.TestCase):
    def test_full_math(self) -> None:
        task = {
            "id": "D-001",
            "startedAt": T_START,
            "readyAt": T_READY,
            "finishedAt": T_FINISH,
            "readyCount": 1,
            "blocks": [
                {"reason": "x", "blockedAt": T_BLOCK, "unblockedAt": T_UNBLOCK},
            ],
        }
        stats = _stats.compute_stats(task)
        self.assertEqual(stats["elapsedTotalSeconds"], 300)
        self.assertEqual(stats["elapsedBlockedSeconds"], 60)
        self.assertEqual(stats["activeTimeSeconds"], 240)
        self.assertEqual(stats["blockCount"], 1)
        self.assertEqual(stats["unblockCount"], 1)
        self.assertEqual(stats["readyCount"], 1)

    def test_backfill_null_for_legacy_task(self) -> None:
        # Task pre-D-052: nenhum campo de timing. Nada e inventado.
        legacy = {"id": "F-001", "status": "Validada"}
        stats = _stats.compute_stats(legacy)
        self.assertIsNone(stats["startedAt"])
        self.assertIsNone(stats["finishedAt"])
        self.assertIsNone(stats["elapsedTotalSeconds"])
        self.assertIsNone(stats["elapsedBlockedSeconds"])
        self.assertIsNone(stats["activeTimeSeconds"])
        self.assertEqual(stats["blockCount"], 0)
        self.assertEqual(stats["readyCount"], 0)

    def test_open_block_does_not_count(self) -> None:
        # Bloqueio sem unblockedAt nao entra na soma (intervalo aberto).
        task = {
            "id": "D-002",
            "startedAt": T_START,
            "blocks": [{"reason": "y", "blockedAt": T_BLOCK}],
        }
        stats = _stats.compute_stats(task)
        self.assertIsNone(stats["elapsedBlockedSeconds"])
        self.assertEqual(stats["blockCount"], 1)
        self.assertEqual(stats["unblockCount"], 0)


def _seed(sandbox: Path) -> None:
    (sandbox / "core" / "src").mkdir(parents=True)
    (sandbox / "core" / "lock").mkdir(parents=True)
    for src in CORE_SRC.glob("*.py"):
        if not src.name.startswith("__"):
            shutil.copy2(src, sandbox / "core" / "src" / src.name)
    shutil.copy2(LOCK_API, sandbox / "core" / "lock" / LOCK_API.name)


def _run(sandbox: Path, *args: str, now: str | None = None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    if now is not None:
        env["GUIA_NOW"] = now
    else:
        env.pop("GUIA_NOW", None)
    return subprocess.run(
        [sys.executable, "core/src/guia.py", *args],
        cwd=sandbox,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )


class LifecycleTimingIntegrationTests(unittest.TestCase):
    def test_create_block_unblock_ready_finish_math(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            # create ja em desenvolvimento -> startedAt = T_START
            r = _run(sandbox, "feature", "Cronometrada", now=T_START)
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            _run(sandbox, "block", "D-001", "--reason", "espera", now=T_BLOCK)
            _run(sandbox, "unblock", "D-001", now=T_UNBLOCK)
            _run(sandbox, "ready", "D-001", "--summary", "ok", now=T_READY)
            rf = _run(sandbox, "finish", "D-001", "--no-commit", now=T_FINISH)
            self.assertEqual(rf.returncode, 0, msg=rf.stderr)

            rs = _run(sandbox, "stats", "D-001", "--json")
            self.assertEqual(rs.returncode, 0, msg=rs.stderr)
            stats = json.loads(rs.stdout)["stats"]
            self.assertEqual(stats["startedAt"], T_START)
            self.assertEqual(stats["readyAt"], T_READY)
            self.assertEqual(stats["finishedAt"], T_FINISH)
            self.assertEqual(stats["elapsedTotalSeconds"], 300)
            self.assertEqual(stats["elapsedBlockedSeconds"], 60)
            self.assertEqual(stats["activeTimeSeconds"], 240)
            self.assertEqual(stats["blockCount"], 1)
            self.assertEqual(stats["unblockCount"], 1)
            self.assertEqual(stats["readyCount"], 1)

    def test_unblock_does_not_reset_started(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _run(sandbox, "feature", "Resumo", now=T_START)
            _run(sandbox, "block", "D-001", "--reason", "espera", now=T_BLOCK)
            _run(sandbox, "unblock", "D-001", now=T_UNBLOCK)
            task = json.loads(_run(sandbox, "tasks", "show", "D-001", "--json").stdout)
            # startedAt segue o inicio original, nao o desbloqueio.
            self.assertEqual(task["startedAt"], T_START)

    def test_started_stamped_on_start_from_backlog(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            # Nasce em backlog: startedAt = null.
            _run(sandbox, "feature", "Parqueada", "--status", "backlog", now=T_START)
            parked = json.loads(_run(sandbox, "tasks", "show", "D-001", "--json").stdout)
            self.assertIsNone(parked["startedAt"])
            # start carimba o inicio.
            _run(sandbox, "start", "D-001", now=T_READY)
            started = json.loads(_run(sandbox, "tasks", "show", "D-001", "--json").stdout)
            self.assertEqual(started["startedAt"], T_READY)

    def test_cancel_sets_finished(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            _seed(sandbox)
            _run(sandbox, "init", "--project-name", "t")
            _run(sandbox, "feature", "Descartada", now=T_START)
            _run(sandbox, "cancel", "D-001", "--reason", "fora de escopo", now=T_FINISH)
            task = json.loads(_run(sandbox, "tasks", "show", "D-001", "--json").stdout)
            self.assertEqual(task["finishedAt"], T_FINISH)


if __name__ == "__main__":
    unittest.main()
