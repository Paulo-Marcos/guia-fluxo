"""D-211: o escopo da regua do delta, levantado pela 4a e 5a auditorias da D-207.

Cada teste segura uma regra que uma mutacao podia tirar sem a suite perceber:
o `git log` das marcas `[unlock:]` que falhava aberto, cada caminho sensivel
novo, o mapa de espelhos (`delivery.audit.mirrors`: copia gerada identica a
fonte conta uma vez so), o binario medido pelo blob e o comando de leitura
do auditor sem textconv nem diff externo.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from conftest_paths import CORE_SRC

sys.path.insert(0, str(CORE_SRC))

from _audit_delta import _sensitive, delta_plan  # noqa: E402

MIRRORS = {"delivery": {"audit": {"mirrors": {"plugins/guia/bin/": "core/src/"}}}}

# Um caminho por padrao novo, que so ele casa: tirar o padrao derruba o caso.
NEW_SENSITIVE = {
    "**/_git_ops.py": "core/src/_git_ops.py",
    "**/_state.py": "plugins/guia/bin/_state.py",
    "**/_constants.py": "core/src/_constants.py",
    "**/_tasks.py": "core/src/_tasks.py",
    "**/_changelog.py": "core/src/_changelog.py",
    "**/_github.py": "core/src/_github.py",
    "**/_auto_finish.py": "core/src/_auto_finish.py",
    "**/_skills.py": "core/src/_skills.py",
    "**/_conductor.py": "core/src/_conductor.py",
    "**/guia.py": "core/src/guia.py",
    "**/guia.ps1": "core/bin/guia.ps1",
    "core/manifest/**": "core/manifest/verbs.yaml",
    "**/audit-checklist.md": "plugins/guia/templates/audit-checklist.md",
    "**/commands/audit.md": "plugins/guia/commands/audit.md",
    "**/.agents/skills/**": "plugins/guia/.agents/skills/guia-ship/SKILL.md",
    "**/templates/locks/**": "core/templates/locks/registry.yaml",
    "**/templates/scaffold/auditoria.yml": "core/templates/scaffold/auditoria.yml",
    "**/.gitmodules": ".gitmodules",
    "**/eslint.config.*": "web/eslint.config.mjs",
    "**/.eslintrc*": "web/.eslintrc.json",
    "**/pyrightconfig.json": "pyrightconfig.json",
    "**/jest.config.*": "web/jest.config.ts",
    "**/vite.config.*": "web/vite.config.ts",
}


class SensitivePathTests(unittest.TestCase):
    def test_each_new_pattern_sends_its_path_to_a_full_audit(self) -> None:
        for pattern, path in NEW_SENSITIVE.items():
            with self.subTest(pattern=pattern):
                self.assertEqual(_sensitive([path], {}), [path])

    def test_each_case_is_held_by_its_own_pattern(self) -> None:
        """Sem o padrao, o caminho do caso nao e sensivel: o caso prova a linha da lista."""
        import _audit_delta

        for pattern, path in NEW_SENSITIVE.items():
            others = tuple(p for p in _audit_delta.DELTA_FULL_PATHS if p != pattern)
            with self.subTest(pattern=pattern), mock.patch.object(_audit_delta, "DELTA_FULL_PATHS", others):
                self.assertEqual(_sensitive([path], {}), [])

    def test_ordinary_module_is_not_sensitive(self) -> None:
        self.assertEqual(_sensitive(["core/src/_task_view.py", "docs/reference/cli.md"], {}), [])


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=", *args],
                            cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _numbered(prefix: str, count: int) -> str:
    return "".join(f"{prefix}{i}\n" for i in range(count))


@unittest.skipUnless(shutil.which("git"), "git nao disponivel")
class DeltaScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _git(self.root, "init", "-q", "-b", "main")
        _git(self.root, "config", "core.autocrlf", "false")
        self._write("leia.txt", _numbered("base", 400))
        self.base = self._commit()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write(self, path: str, text: str) -> None:
        (self.root / path).parent.mkdir(parents=True, exist_ok=True)
        (self.root / path).write_text(text, encoding="utf-8")

    def _commit(self, message: str = "c") -> str:
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-q", "-m", message)
        return _git(self.root, "rev-parse", "HEAD")

    def _plan(self, rejected: str, head: str, config: dict | None = None) -> dict:
        previous = {"result": "rejected", "auditedSha": rejected, "auditedBase": self.base}
        return delta_plan(self.root, previous, {"head": head, "base": self.base}, config or {})

    # --- [unlock:] lido pelo git que falha fechado -------------------------------------------

    def test_git_log_failing_only_on_the_new_side_is_a_full_audit(self) -> None:
        """Antes, `git_output` devolvia None e `or ""` sumia com o `[unlock:]` novo: delta."""
        self._write("app.txt", "um\n")
        rejected = self._commit()
        self._write("app.txt", "dois\n")
        head = self._commit("fix\n\n[unlock:testes-sao-contrato] motivo: x")
        real_run = subprocess.run

        def failing_log(args, *rest, **kwargs):
            if "log" in args and f"{self.base}..{head}" in args:
                return subprocess.CompletedProcess(args, 128, b"" if not kwargs.get("text") else "", "")
            return real_run(args, *rest, **kwargs)

        with mock.patch("subprocess.run", side_effect=failing_log):
            plan = self._plan(rejected, head)
        self.assertEqual(plan["mode"], "full")
        self.assertIn("a medida do delta nao entendeu", plan["reason"])

    # --- espelhos: copia gerada identica a fonte conta uma vez ------------------------------

    def _bulk(self) -> None:
        """O resto do PR, que nao muda: a regra da metade nao se mete nos casos de tamanho."""
        self._write("grande.txt", _numbered("g", 600))

    def _engine_fix(self, lines: int, copy_text: str | None = None) -> tuple[str, str]:
        self._bulk()
        self._write("core/src/mod.py", _numbered("a", lines))
        self._write("plugins/guia/bin/mod.py", _numbered("a", lines))
        rejected = self._commit()
        self._write("core/src/mod.py", _numbered("b", lines))
        self._write("plugins/guia/bin/mod.py", copy_text if copy_text is not None else _numbered("b", lines))
        return rejected, self._commit()

    def test_identical_copy_counts_once(self) -> None:
        """80 linhas trocadas na fonte e na copia: 160 + 160 = 320 > 300 sem o mapa; 160 com ele."""
        rejected, head = self._engine_fix(80)
        self.assertIn("delta grande (320", self._plan(rejected, head)["reason"])
        plan = self._plan(rejected, head, MIRRORS)
        self.assertEqual(plan["mode"], "delta", plan.get("reason"))
        self.assertEqual(plan["lines"], 160)

    def test_identical_copy_still_listed_for_the_sensitive_rule(self) -> None:
        rejected, head = self._engine_fix(80)
        self.assertEqual(self._plan(rejected, head, MIRRORS)["files"], ["core/src/mod.py", "plugins/guia/bin/mod.py"])

    def test_copy_that_diverges_from_the_source_counts_whole(self) -> None:
        rejected, head = self._engine_fix(80, copy_text=_numbered("c", 80))
        self.assertIn("delta grande (320", self._plan(rejected, head, MIRRORS)["reason"])

    def test_copy_that_diverged_at_the_audit_counts_whole(self) -> None:
        """Igual a fonte so no head novo: o que a copia mudou desde a auditoria e mudanca dela."""
        self._bulk()
        self._write("core/src/mod.py", _numbered("a", 80))
        self._write("plugins/guia/bin/mod.py", _numbered("c", 80))
        rejected = self._commit()
        self._write("core/src/mod.py", _numbered("b", 80))
        self._write("plugins/guia/bin/mod.py", _numbered("b", 80))
        self.assertIn("delta grande (320", self._plan(rejected, self._commit(), MIRRORS)["reason"])

    def test_copy_only_change_counts_whole(self) -> None:
        """Mudanca so na copia (o plugin roda dela): nada para descontar."""
        self._bulk()
        self._write("core/src/mod.py", _numbered("a", 200))
        self._write("plugins/guia/bin/mod.py", _numbered("a", 200))
        rejected = self._commit()
        self._write("plugins/guia/bin/mod.py", _numbered("b", 200))
        plan = self._plan(rejected, self._commit(), MIRRORS)
        self.assertIn("delta grande (400", plan["reason"])

    def test_identical_patch_outside_the_map_counts_twice(self) -> None:
        """Sem dedupe generico: o mesmo trecho espalhado fora do mapa mede cada copia."""
        self._bulk()
        self._write("a/mod.py", _numbered("a", 80))
        self._write("b/mod.py", _numbered("a", 80))
        rejected = self._commit()
        self._write("a/mod.py", _numbered("b", 80))
        self._write("b/mod.py", _numbered("b", 80))
        self.assertIn("delta grande (320", self._plan(rejected, self._commit(), MIRRORS)["reason"])

    def test_half_rule_measures_the_pr_without_the_echoes_too(self) -> None:
        """Delta e PR na mesma regua: 60 de 62 (30 + modo de arquivo novo, por lado), nao 60 de 124."""
        self._write("core/src/mod.py", _numbered("a", 30))
        self._write("plugins/guia/bin/mod.py", _numbered("a", 30))
        rejected = self._commit()
        self._write("core/src/mod.py", _numbered("b", 30))
        self._write("plugins/guia/bin/mod.py", _numbered("b", 30))
        plan = self._plan(rejected, self._commit(), MIRRORS)
        self.assertIn("mais da metade do PR (60 de 62", plan["reason"])

    def test_map_onto_itself_discounts_nothing(self) -> None:
        """Copia e fonte no mesmo prefixo: o arquivo seria eco de si mesmo e sumiria da regua."""
        rejected, head = self._engine_fix(80)
        plan = self._plan(rejected, head, {"delivery": {"audit": {"mirrors": {"core/src/": "core/src/"}}}})
        self.assertIn("delta grande (320", plan["reason"])

    def test_malformed_map_counts_everything(self) -> None:
        rejected, head = self._engine_fix(80)
        for mirrors in (["plugins/guia/bin/"], {"plugins/guia/bin/": 3}, "x"):
            with self.subTest(mirrors=mirrors):
                plan = self._plan(rejected, head, {"delivery": {"audit": {"mirrors": mirrors}}})
                self.assertIn("delta grande (320", plan["reason"])

    # --- binario: pelo blob, e mudar binario no delta e completa ----------------------------

    def test_binary_change_in_the_delta_is_a_full_audit(self) -> None:
        (self.root / "logo.bin").write_bytes(b"\x00\x01")
        rejected = self._commit()
        (self.root / "logo.bin").write_bytes(b"\x00\x02")
        plan = self._plan(rejected, self._commit())
        self.assertEqual(plan["mode"], "full")
        self.assertIn("delta toca binario: logo.bin", plan["reason"])

    def test_binary_is_not_read_with_text(self) -> None:
        """`--text` num binario grande e lento e nao muda a decisao: o diff do binario sai sem ele."""
        (self.root / "logo.bin").write_bytes(b"\x00" * 10)
        rejected = self._commit()
        (self.root / "logo.bin").write_bytes(b"\x00\x01" * 10)
        head = self._commit()
        real_run = subprocess.run
        calls: list[list[str]] = []

        def spy(args, *rest, **kwargs):
            calls.append(list(args))
            return real_run(args, *rest, **kwargs)

        with mock.patch("subprocess.run", side_effect=spy):
            self._plan(rejected, head)
        per_file = [c for c in calls if any(a.endswith("logo.bin") for a in c) and "--unified=0" in c]
        self.assertTrue(per_file)
        self.assertTrue(all("--text" not in c for c in per_file), per_file)

    def test_text_hidden_by_no_diff_is_measured_not_binary(self) -> None:
        """`*.py -diff` e texto: medido com `--text` (o `textDiff` mostra a linha), nao vira completa."""
        self._write(".gitattributes", "*.py -diff\n")
        self.base = self._commit()
        self._write("x.py", "valor = 1\n")
        rejected = self._commit()
        self._write("x.py", "valor = 2\n")
        plan = self._plan(rejected, self._commit())
        self.assertEqual((plan["mode"], plan["lines"]), ("delta", 2), plan.get("reason"))

    def test_check_attr_failing_is_a_full_audit(self) -> None:
        (self.root / "logo.bin").write_bytes(b"\x00\x01")
        rejected = self._commit()
        (self.root / "logo.bin").write_bytes(b"\x00\x01")
        self._write("app.txt", "dois\n")
        head = self._commit()
        real_run = subprocess.run

        def failing_attr(args, *rest, **kwargs):
            if "check-attr" in args:
                return subprocess.CompletedProcess(args, 128, b"", b"fatal")
            return real_run(args, *rest, **kwargs)

        with mock.patch("subprocess.run", side_effect=failing_attr):
            plan = self._plan(rejected, head)
        self.assertEqual(plan["mode"], "full")
        self.assertIn("git check-attr falhou", plan["reason"])

    def test_unchanged_binary_stays_a_delta(self) -> None:
        (self.root / "logo.bin").write_bytes(b"\x00\x01")
        self._write("app.txt", "um\n")
        rejected = self._commit()
        self._write("app.txt", "dois\n")
        self.assertEqual(self._plan(rejected, self._commit())["mode"], "delta")

    # --- comando de leitura do auditor -----------------------------------------------------

    def test_text_diff_skips_textconv_and_external_diff(self) -> None:
        """No Git for Windows o astextplain (textconv) faz o `git diff --text` falhar."""
        self._write("app.txt", "um\n")
        rejected = self._commit()
        self._write("app.txt", "dois\n")
        head = self._commit()
        self.assertEqual(self._plan(rejected, head)["textDiff"],
                         f"git diff --text --no-textconv --no-ext-diff {rejected} {head}")


if __name__ == "__main__":
    unittest.main()
