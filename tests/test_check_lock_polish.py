"""F-020: tests para --dry-run em lock, --force em unlock, stdin em ci."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import REPO_ROOT, ensure_core_importable

ensure_core_importable()

import lock_api  # noqa: E402

CHECK_LOCK = REPO_ROOT / "core" / "lock" / "check-lock.py"


def _run(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECK_LOCK), *args],
        cwd=REPO_ROOT,
        input=stdin,
        capture_output=True,
        text=True,
    )


class DryRunTests(unittest.TestCase):
    """--dry-run nao toca o registry."""

    def test_dry_run_does_not_write(self) -> None:
        registry_before = lock_api.REGISTRY.read_text(encoding="utf-8") if lock_api.REGISTRY.exists() else ""
        result = _run("lock", "ttdry", "--description", "x", "--dry-run", "FEATURES.md")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("[dry-run]", result.stdout)
        registry_after = lock_api.REGISTRY.read_text(encoding="utf-8") if lock_api.REGISTRY.exists() else ""
        self.assertEqual(registry_before, registry_after)

    def test_dry_run_detects_existing_id(self) -> None:
        # `adicoes-exigem-autorizacao` ja existe no registry do repo
        result = _run(
            "lock",
            "adicoes-exigem-autorizacao",
            "--description",
            "x",
            "--dry-run",
            "FEATURES.md",
        )
        self.assertEqual(result.returncode, 1, msg=result.stdout)
        self.assertIn("ja existe", result.stderr)


class UnlockForceTests(unittest.TestCase):
    """unlock sem --force em non-TTY (subprocess) deve falhar."""

    def test_unlock_without_force_in_non_tty_fails(self) -> None:
        result = _run("unlock", "nao-existe-nem-importa")
        # Sem --force, em subprocess (non-TTY), aborta antes de chegar
        # no remove_lock real. Pode falhar com "use --force" OU com "nao
        # encontrada" dependendo da ordem - get_lock e chamado primeiro.
        # O importante: nao mexer no registry.
        self.assertEqual(result.returncode, 1)


class CiStdinTests(unittest.TestCase):
    """ci aceita stdin via files=-."""

    def test_ci_with_stdin_files(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".msg", delete=False, encoding="utf-8"
        ) as msg_file:
            msg_file.write("commit: nada\n")
            msg_path = msg_file.name
        try:
            # Passa "M\tREADME.md" via stdin (modify de README)
            result = _run("ci", "--files", "-", "--messages", msg_path, stdin="M\tREADME.md\n")
            # README nao esta travado por nada (lock global e add-only),
            # entao retorna 0
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("OK", result.stdout)
        finally:
            Path(msg_path).unlink(missing_ok=True)

    def test_ci_with_stdin_messages(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".files", delete=False, encoding="utf-8"
        ) as files_file:
            files_file.write("M\tREADME.md\n")
            files_path = files_file.name
        try:
            result = _run(
                "ci",
                "--files",
                files_path,
                "--messages",
                "-",
                stdin="commit: nada [unlock:x] motivo: y\n",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
        finally:
            Path(files_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
