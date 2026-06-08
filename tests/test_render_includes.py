"""D-047: testes da diretiva {{include: <path>}} em render-skills.py.

Cobre:
- Expansao basica de include em sandbox isolado.
- Path resolution: relativo ao **diretorio do arquivo que inclui**
  (intuicao: body em bodies/foo.md fazendo {{include: _partials/x.md}}
  pega bodies/_partials/x.md; partial em bodies/_partials/a.md fazendo
  {{include: b.md}} pega bodies/_partials/b.md).
- Includes recursivos (partial dentro de partial).
- Guards: path traversal bloqueado, arquivo nao encontrado, ciclo.
- Invariante de saida: nenhum `{{include:` literal sobrevive em dist/.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conftest_paths import REPO_ROOT

RENDER = REPO_ROOT / "core" / "build" / "render-skills.py"
DIST = REPO_ROOT / "dist"


def _load_render_module(module_name: str):
    """Carrega render-skills.py como modulo importavel (alguns testes
    precisam mexer em MANIFEST_DIR / MANIFEST_FILE para sandboxar).
    """
    spec = importlib.util.spec_from_file_location(module_name, RENDER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _sandbox_manifest(tmp: Path, bodies: dict[str, str], manifest_yaml: str) -> tuple[Path, Path]:
    """Cria uma pasta core/manifest/ sandbox com bodies e manifest.

    bodies: { caminho_relativo_a_bodies/: conteudo }
    Retorna (manifest_dir, manifest_file).
    """
    manifest_dir = tmp / "manifest"
    bodies_dir = manifest_dir / "bodies"
    bodies_dir.mkdir(parents=True)
    for rel, content in bodies.items():
        target = bodies_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    manifest_file = manifest_dir / "manifest.yaml"
    manifest_file.write_text(manifest_yaml, encoding="utf-8")
    return manifest_dir, manifest_file


def _render_in_sandbox(manifest_dir: Path, manifest_file: Path, module_name: str):
    """Executa collect_outputs apos patchear MANIFEST_DIR / MANIFEST."""
    module = _load_render_module(module_name)
    module.MANIFEST_DIR = manifest_dir
    module.MANIFEST = manifest_file
    try:
        manifest_data = module.load_manifest()
        return module.collect_outputs(manifest_data)
    finally:
        sys.modules.pop(module_name, None)


_MINIMAL_MANIFEST = """\
version: 2
verbs:
  test:
    description: |
      Test description.
    targets:
      claude_skill:
        body_file: bodies/test.claude.md
"""


class BasicIncludeTests(unittest.TestCase):
    def test_simple_include_expands_inline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mdir, mfile = _sandbox_manifest(
                Path(tmp),
                {
                    "test.claude.md": "# Test\n\n{{include: _partials/p.md}}\n\nAfter.\n",
                    "_partials/p.md": "Inside partial.",
                },
                _MINIMAL_MANIFEST,
            )
            outputs = _render_in_sandbox(mdir, mfile, "render_probe_basic")
            self.assertEqual(len(outputs), 1)
            content = outputs[0].content
            self.assertIn("Inside partial.", content)
            self.assertIn("After.", content)
            self.assertNotIn("{{include:", content, msg="raw directive leaked into output")

    def test_inline_directive_in_prose_is_left_alone(self) -> None:
        """A regex tem ancoras ^/$ com MULTILINE: so dispara quando a
        diretiva ocupa a linha inteira. Mencao em prosa fica intacta -
        evita falso positivo em docs que descrevem o proprio mecanismo.
        """
        with tempfile.TemporaryDirectory() as tmp:
            mdir, mfile = _sandbox_manifest(
                Path(tmp),
                {
                    "test.claude.md": (
                        "# Test\n\n"
                        "Para incluir um partial use `{{include: foo.md}}` na linha sozinha.\n"
                        "Fim.\n"
                    ),
                },
                _MINIMAL_MANIFEST,
            )
            # Nao precisa criar foo.md - a regex nao deve pegar a mencao
            # inline na prosa (ela esta no meio de um paragrafo com texto
            # antes e depois). Se a regex pegasse, faltaria foo.md e o
            # renderer abortaria.
            outputs = _render_in_sandbox(mdir, mfile, "render_probe_inline_prose")
            content = outputs[0].content
            # A mencao em prosa sobrevive intacta no output.
            self.assertIn("{{include: foo.md}}", content)


class PathResolutionTests(unittest.TestCase):
    """O bug original: include resolvido relativo a MANIFEST_DIR em vez
    do arquivo que inclui. Agora deve ser relativo ao arquivo que inclui."""

    def test_include_resolves_relative_to_including_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mdir, mfile = _sandbox_manifest(
                Path(tmp),
                {
                    "test.claude.md": "{{include: _partials/x.md}}\n",
                    "_partials/x.md": "Partial X.",
                },
                _MINIMAL_MANIFEST,
            )
            outputs = _render_in_sandbox(mdir, mfile, "render_probe_relpath")
            self.assertIn("Partial X.", outputs[0].content)

    def test_partial_can_include_sibling_partial(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mdir, mfile = _sandbox_manifest(
                Path(tmp),
                {
                    "test.claude.md": "{{include: _partials/a.md}}\n",
                    "_partials/a.md": "Top of A.\n{{include: b.md}}\nBottom of A.",
                    "_partials/b.md": "From sibling B.",
                },
                _MINIMAL_MANIFEST,
            )
            outputs = _render_in_sandbox(mdir, mfile, "render_probe_sibling")
            content = outputs[0].content
            self.assertIn("Top of A.", content)
            self.assertIn("From sibling B.", content)
            self.assertIn("Bottom of A.", content)


class GuardTests(unittest.TestCase):
    def test_missing_partial_aborts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mdir, mfile = _sandbox_manifest(
                Path(tmp),
                {"test.claude.md": "{{include: _partials/missing.md}}\n"},
                _MINIMAL_MANIFEST,
            )
            module = _load_render_module("render_probe_missing")
            module.MANIFEST_DIR = mdir
            module.MANIFEST = mfile
            try:
                with self.assertRaises(SystemExit) as ctx:
                    module.collect_outputs(module.load_manifest())
                self.assertEqual(ctx.exception.code, 2)
            finally:
                sys.modules.pop("render_probe_missing", None)

    def test_path_traversal_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mdir, mfile = _sandbox_manifest(
                Path(tmp),
                {"test.claude.md": "{{include: ../../etc/passwd}}\n"},
                _MINIMAL_MANIFEST,
            )
            module = _load_render_module("render_probe_traversal")
            module.MANIFEST_DIR = mdir
            module.MANIFEST = mfile
            try:
                with self.assertRaises(SystemExit) as ctx:
                    module.collect_outputs(module.load_manifest())
                self.assertEqual(ctx.exception.code, 2)
            finally:
                sys.modules.pop("render_probe_traversal", None)

    def test_circular_include_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mdir, mfile = _sandbox_manifest(
                Path(tmp),
                {
                    "test.claude.md": "{{include: _partials/a.md}}\n",
                    "_partials/a.md": "{{include: b.md}}",
                    "_partials/b.md": "{{include: a.md}}",
                },
                _MINIMAL_MANIFEST,
            )
            module = _load_render_module("render_probe_cycle")
            module.MANIFEST_DIR = mdir
            module.MANIFEST = mfile
            try:
                with self.assertRaises(SystemExit) as ctx:
                    module.collect_outputs(module.load_manifest())
                self.assertEqual(ctx.exception.code, 2)
            finally:
                sys.modules.pop("render_probe_cycle", None)


class DistInvariantTests(unittest.TestCase):
    """Invariante de saida: nenhum SKILL.md em dist/ deve conter um
    {{include: literal nao expandido. Garante que toda diretiva escrita
    nos bodies foi resolvida no build."""

    def _all_dist_skill_files(self) -> list[Path]:
        candidates: list[Path] = []
        for root in (DIST / "skills", DIST / ".agents" / "skills"):
            if root.exists():
                candidates.extend(root.rglob("SKILL.md"))
        return candidates

    def test_no_unexpanded_include_in_dist(self) -> None:
        # Garante que o dist/ atual foi renderizado (CI usa --check).
        result = subprocess.run(
            [sys.executable, str(RENDER), "--check"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=f"dist/ esta stale antes do teste: {result.stderr}",
        )
        for skill_file in self._all_dist_skill_files():
            text = skill_file.read_text(encoding="utf-8")
            self.assertNotIn(
                "{{include:",
                text,
                msg=f"directive nao-expandida sobrevive em {skill_file.relative_to(REPO_ROOT)}",
            )


if __name__ == "__main__":
    unittest.main()
