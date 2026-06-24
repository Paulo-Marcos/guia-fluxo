"""D-095: `finish` aciona uma validacao consultiva de qualidade antes de fechar.

O dono quer que o finish SEMPRE valide qualidade do que foi feito (alem dos
comandos de teste). Skills sao acionadas pelo AGENTE, entao o core sinaliza+
exige: recusa o fechamento ate o agente confirmar (--quality-checked /
--quality-skill) ou pular explicitamente (--quality-skip). Estado da task nao
muda quando o gate barra (mesma garantia do docs-gate e do gate humano D-080).

Duas camadas de teste:
  - Unit, sobre _quality_hook (logica pura do gate/record).
  - Integracao, rodando o CLI real num sandbox com repo git de verdade.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import REPO_ROOT, ensure_core_importable

ensure_core_importable()

import _quality_hook  # noqa: E402
from _constants import KIND_CHORE  # noqa: E402

CORE_SRC = REPO_ROOT / "core" / "src"
CORE_LOCK = REPO_ROOT / "core" / "lock"


def _task(**overrides):
    base = {"id": "D-001", "kind": KIND_CHORE, "title": "T", "modifiedFiles": ["src/a.py"]}
    base.update(overrides)
    return base


def _args(**kwargs):
    return argparse.Namespace(
        quality_checked=kwargs.get("quality_checked", False),
        quality_skill=kwargs.get("quality_skill", []),
        quality_finding=kwargs.get("quality_finding", []),
        quality_skip=kwargs.get("quality_skip", None),
    )


def _config(enabled: bool = True):
    return {"finish": {"qualityGateByDefault": enabled}}


class QualityGateUnitTests(unittest.TestCase):
    def test_blocks_when_product_files_and_no_signal(self) -> None:
        with self.assertRaises(SystemExit):
            _quality_hook.ensure_quality_review_ok(_task(), [], _config(), _args())

    def test_passes_when_checked(self) -> None:
        _quality_hook.ensure_quality_review_ok(
            _task(), [], _config(), _args(quality_checked=True)
        )

    def test_passes_when_skill_listed(self) -> None:
        _quality_hook.ensure_quality_review_ok(
            _task(), [], _config(), _args(quality_skill=["clean-code-review"])
        )

    def test_passes_with_explicit_skip(self) -> None:
        _quality_hook.ensure_quality_review_ok(
            _task(), [], _config(), _args(quality_skip="so renomeou variavel")
        )

    def test_noop_when_only_guia_bookkeeping_changed(self) -> None:
        """Catalogo/estado do Guia (.guia/**) nao e produto: nao dispara o gate."""
        task = _task(modifiedFiles=[".guia/DEMANDAS.md", ".guia/tasks.json"])
        _quality_hook.ensure_quality_review_ok(task, [], _config(), _args())

    def test_noop_when_gate_disabled(self) -> None:
        _quality_hook.ensure_quality_review_ok(
            _task(), [], _config(enabled=False), _args()
        )

    def test_candidates_merge_and_filter(self) -> None:
        cands = _quality_hook.compute_quality_candidates(
            _task(modifiedFiles=["src/a.py", ".guia/tasks.json"]),
            ["src/b.py", "src/a.py"],
        )
        self.assertEqual(cands, ["src/a.py", "src/b.py"])

    def test_record_captures_skills_and_skip(self) -> None:
        record = _quality_hook.build_quality_review_record(
            _task(),
            [],
            _args(quality_skill=["clean-code-review"], quality_skip="n/a"),
        )
        self.assertEqual(record["skills"], ["clean-code-review"])
        self.assertEqual(record["skipped"], "n/a")
        self.assertTrue(record["dimensions"])  # 5 dimensoes a-e


def _seed(sandbox: Path) -> None:
    (sandbox / "core" / "src").mkdir(parents=True)
    (sandbox / "core" / "lock").mkdir(parents=True)
    for src in CORE_SRC.glob("*.py"):
        if not src.name.startswith("__"):
            shutil.copy2(src, sandbox / "core" / "src" / src.name)
    shutil.copy2(CORE_LOCK / "lock_api.py", sandbox / "core" / "lock" / "lock_api.py")


def _git(sandbox: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=sandbox, capture_output=True, text=True, encoding="utf-8"
    )


def _init_repo(sandbox: Path) -> None:
    _git(sandbox, "init")
    _git(sandbox, "config", "user.email", "test@example.com")
    _git(sandbox, "config", "user.name", "Test")
    _git(sandbox, "config", "commit.gpgsign", "false")


def _run(sandbox: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "core/src/guia.py", *args],
        cwd=sandbox,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _status(sandbox: Path, task_id: str) -> str:
    return json.loads(_run(sandbox, "tasks", "show", task_id, "--json").stdout)["status"]


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class QualityGateCliTests(unittest.TestCase):
    def _prepare(self, sandbox: Path) -> None:
        _seed(sandbox)
        _init_repo(sandbox)
        (sandbox / "feature.txt").write_text("v1\n", encoding="utf-8")
        _git(sandbox, "add", "feature.txt")
        _git(sandbox, "commit", "-m", "seed")
        _run(sandbox, "chore", "Mexe no feature.txt")
        (sandbox / "feature.txt").write_text("v2\n", encoding="utf-8")

    def test_finish_refused_without_quality_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            self._prepare(sandbox)
            result = _run(
                sandbox, "finish", "D-001", "--no-commit",
                "--file", "feature.txt", "--docs-skip", "n/a",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("quality-check", result.stderr + result.stdout)
            # Gate barra antes de mutar status.
            self.assertEqual(_status(sandbox, "D-001"), "Em desenvolvimento")

    def test_finish_accepted_with_quality_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            self._prepare(sandbox)
            result = _run(
                sandbox, "finish", "D-001", "--no-commit",
                "--file", "feature.txt", "--docs-skip", "n/a",
                "--quality-checked", "--quality-skill", "clean-code-review",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(_status(sandbox, "D-001"), "Validada")
            task = _json_task(sandbox, "D-001")
            self.assertIn("clean-code-review", task["qualityReview"]["skills"])

    def test_finish_accepted_with_explicit_skip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            self._prepare(sandbox)
            result = _run(
                sandbox, "finish", "D-001", "--no-commit",
                "--file", "feature.txt", "--docs-skip", "n/a",
                "--quality-skip", "alteracao trivial de constante",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(_status(sandbox, "D-001"), "Validada")
            task = _json_task(sandbox, "D-001")
            self.assertEqual(
                task["qualityReview"]["skipped"], "alteracao trivial de constante"
            )


def _json_task(sandbox: Path, task_id: str) -> dict:
    return json.loads(_run(sandbox, "tasks", "show", task_id, "--json").stdout)


if __name__ == "__main__":
    unittest.main()
