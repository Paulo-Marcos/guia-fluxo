"""D-059: testes das lacunas de hardening do render-skills.py.

Cobre cinco garantias que o refactor (config injetavel + RenderError +
registro de targets) deixou explicitas e que antes nao tinham teste:

1. --clean e opt-in: rodar SEM a flag preserva orfaos em dist/.
2. wrapper sem o marcador esperado aborta (RenderError).
3. frontmatter tentando sobrescrever chave reservada aborta (RenderError).
4. write_outputs e idempotente: segunda renderizacao nao grava nada.
5. template nao declarado em TEMPLATE_FILES aborta (RenderError).

Os caminhos de erro sao testados no nivel de unidade (chamando as
funcoes direto) porque a nova API lanca RenderError em vez de encerrar o
processo - mais rapido e mais preciso que inspecionar stderr via subprocess.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from conftest_paths import REPO_ROOT

RENDER = REPO_ROOT / "core" / "build" / "render-skills.py"


def _load_render_module(module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, RENDER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RENDER), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


class CleanIsOptInTests(unittest.TestCase):
    """Operacao destrutiva so dispara com a flag. Sem --clean, o orfao
    sobrevive - garante que o default e seguro."""

    def test_render_without_clean_preserves_orphan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            self.assertEqual(_run("--output-dir", str(out)).returncode, 0)
            orphan_dir = out / ".agents" / "skills" / "guia-verbo-fantasma"
            orphan_dir.mkdir(parents=True)
            orphan = orphan_dir / "SKILL.md"
            orphan.write_text("fantasma", encoding="utf-8")
            # Render de novo SEM --clean.
            result = _run("--output-dir", str(out))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(orphan.exists(), msg="--clean nao deveria ter rodado sem a flag")


class WriteIdempotenceTests(unittest.TestCase):
    """Segunda renderizacao consecutiva nao grava nada (write_outputs so
    escreve quando o conteudo difere)."""

    def test_second_render_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            first = _run("--output-dir", str(out))
            self.assertEqual(first.returncode, 0, msg=first.stderr)
            self.assertIn("Renderizados", first.stdout)
            second = _run("--output-dir", str(out))
            self.assertEqual(second.returncode, 0, msg=second.stderr)
            self.assertIn("Nada gravado", second.stdout)


class WrapperMarkerTests(unittest.TestCase):
    """_adapt_wrapper_for_plugin aborta se o marcador some - protege o
    invariante de que dist/bin/guia.ps1 resolve guia.py no layout flat."""

    def test_missing_marker_raises(self) -> None:
        module = _load_render_module("render_probe_wrapper")
        try:
            with self.assertRaises(module.RenderError):
                module._adapt_wrapper_for_plugin("conteudo sem o marcador esperado\n")
        finally:
            sys.modules.pop("render_probe_wrapper", None)

    def test_present_marker_is_rewritten(self) -> None:
        module = _load_render_module("render_probe_wrapper_ok")
        try:
            src = f"python {module.WRAPPER_MARKER} @args"
            out = module._adapt_wrapper_for_plugin(src)
            self.assertIn(module.WRAPPER_REPLACEMENT, out)
            self.assertNotIn(module.WRAPPER_MARKER, out)
        finally:
            sys.modules.pop("render_probe_wrapper_ok", None)


class ReservedFrontmatterTests(unittest.TestCase):
    """render_skill_md aborta se o frontmatter extra tentar sobrescrever
    name/description (geradas pelo renderer)."""

    def test_extra_name_raises(self) -> None:
        module = _load_render_module("render_probe_reserved_name")
        try:
            with self.assertRaises(module.RenderError):
                module.render_skill_md("n", "desc", "body", "verb", extras={"name": "x"})
        finally:
            sys.modules.pop("render_probe_reserved_name", None)

    def test_extra_description_raises(self) -> None:
        module = _load_render_module("render_probe_reserved_desc")
        try:
            with self.assertRaises(module.RenderError):
                module.render_skill_md("n", "desc", "body", "verb", extras={"description": "x"})
        finally:
            sys.modules.pop("render_probe_reserved_desc", None)

    def test_empty_description_raises(self) -> None:
        module = _load_render_module("render_probe_empty_desc")
        try:
            with self.assertRaises(module.RenderError):
                module.render_skill_md("n", "   ", "body", "verb")
        finally:
            sys.modules.pop("render_probe_empty_desc", None)


class TemplateSetValidationTests(unittest.TestCase):
    """_validate_template_set aborta quando core/templates/ tem arquivo
    nao declarado em TEMPLATE_FILES (evita drift silencioso de templates)."""

    def test_undeclared_template_raises(self) -> None:
        module = _load_render_module("render_probe_templates")
        try:
            with tempfile.TemporaryDirectory() as tmp:
                templates_src = Path(tmp) / "templates"
                # Cria os arquivos declarados + um nao declarado.
                for rel, _dst in module.TEMPLATE_FILES:
                    target = templates_src / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text("ok\n", encoding="utf-8")
                bogus = templates_src / "locks" / "nao-declarado.txt"
                bogus.write_text("surpresa\n", encoding="utf-8")
                paths = replace(module.Paths.build(REPO_ROOT), templates_src=templates_src)
                with self.assertRaises(module.RenderError):
                    module._validate_template_set(paths)
        finally:
            sys.modules.pop("render_probe_templates", None)

    def test_only_declared_templates_passes(self) -> None:
        module = _load_render_module("render_probe_templates_ok")
        try:
            with tempfile.TemporaryDirectory() as tmp:
                templates_src = Path(tmp) / "templates"
                for rel, _dst in module.TEMPLATE_FILES:
                    target = templates_src / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text("ok\n", encoding="utf-8")
                paths = replace(module.Paths.build(REPO_ROOT), templates_src=templates_src)
                # Nao deve levantar.
                module._validate_template_set(paths)
        finally:
            sys.modules.pop("render_probe_templates_ok", None)


if __name__ == "__main__":
    unittest.main()
