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
from dataclasses import replace
from pathlib import Path

from conftest_paths import REPO_ROOT

RENDER = REPO_ROOT / "core" / "build" / "render-skills.py"
DIST = REPO_ROOT / "plugins" / "guia"


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


def _paths_for(module, manifest_dir: Path, manifest_file: Path):
    """Constroi um Paths apontando o manifest para o sandbox (D-059).

    Substitui o antigo monkeypatch de globais (module.MANIFEST_DIR/MANIFEST)
    pela injecao explicita de config que a nova API exige.
    """
    base = module.Paths.build(REPO_ROOT)
    return replace(
        base,
        manifest_dir=manifest_dir,
        manifest=manifest_file,
        bodies_dir=manifest_dir / "bodies",
    )


def _render_in_sandbox(manifest_dir: Path, manifest_file: Path, module_name: str):
    """Executa collect_outputs com Paths apontado para o sandbox."""
    module = _load_render_module(module_name)
    paths = _paths_for(module, manifest_dir, manifest_file)
    try:
        manifest_data = module.load_manifest(paths)
        return module.collect_outputs(manifest_data, paths)
    finally:
        sys.modules.pop(module_name, None)


_MINIMAL_MANIFEST = """\
version: 2
verbs:
  test:
    description: |
      Test description.
    targets:
      claude_command:
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
            paths = _paths_for(module, mdir, mfile)
            try:
                with self.assertRaises(module.RenderError):
                    module.collect_outputs(module.load_manifest(paths), paths)
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
            paths = _paths_for(module, mdir, mfile)
            try:
                with self.assertRaises(module.RenderError):
                    module.collect_outputs(module.load_manifest(paths), paths)
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
            paths = _paths_for(module, mdir, mfile)
            try:
                with self.assertRaises(module.RenderError):
                    module.collect_outputs(module.load_manifest(paths), paths)
            finally:
                sys.modules.pop("render_probe_cycle", None)

    def test_circular_chain_uses_resolved_manifest_dir(self) -> None:
        """Regressao D-072: o chain do ciclo relativiza contra o manifest_dir
        RESOLVIDO. No runner Windows o tempdir vem em nome curto 8.3 (RUNNER~1)
        e .resolve() expande pro longo, fazendo manifest_dir cru != paths
        resolvidos -> relative_to estourava ValueError em vez de RenderError.
        Forcamos o descasamento de forma portatil com um componente '..' no
        manifest_dir cru (textualmente != .resolve(), mesmo destino).
        """
        with tempfile.TemporaryDirectory() as tmp:
            mdir = Path(tmp) / "manifest"
            partials = mdir / "bodies" / "_partials"
            partials.mkdir(parents=True)
            (partials / "a.md").write_text("{{include: b.md}}", encoding="utf-8")
            (partials / "b.md").write_text("{{include: a.md}}", encoding="utf-8")
            module = _load_render_module("render_probe_cycle_unresolved")
            unresolved = mdir.parent / "x" / ".." / "manifest"
            try:
                with self.assertRaises(module.RenderError):
                    module._expand_includes(
                        "{{include: _partials/a.md}}\n",
                        origin=mdir / "bodies" / "seed.md",
                        manifest_dir=unresolved,
                        body_cache={},
                    )
            finally:
                sys.modules.pop("render_probe_cycle_unresolved", None)


_DUAL_TARGET_MANIFEST = """\
version: 2
verbs:
  test:
    description: |
      Test description.
    targets:
      agent_skill:
        body_file: bodies/test.md
      claude_command:
        body_file: bodies/test.md
"""


class IncludePerTargetTests(unittest.TestCase):
    """D-050: {{include_per_target: <base>}} resolve para
    <base>.agent.md ou <base>.claude.md conforme o target sendo
    renderizado. Permite 1 body por verbo apontando aos 2 targets."""

    def test_resolves_to_agent_partial_for_agent_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mdir, mfile = _sandbox_manifest(
                Path(tmp),
                {
                    "test.md": "Start.\n\n{{include_per_target: _partials/p}}\n\nEnd.\n",
                    "_partials/p.agent.md": "AGENT-specific.",
                    "_partials/p.claude.md": "CLAUDE-specific.",
                },
                _DUAL_TARGET_MANIFEST,
            )
            outputs = _render_in_sandbox(mdir, mfile, "render_probe_pertarget_agent")
            agent_out = next(o for o in outputs if o.target == "agent_skill")
            claude_out = next(o for o in outputs if o.target == "claude_command")
            self.assertIn("AGENT-specific.", agent_out.content)
            self.assertNotIn("CLAUDE-specific.", agent_out.content)
            self.assertIn("CLAUDE-specific.", claude_out.content)
            self.assertNotIn("AGENT-specific.", claude_out.content)

    def test_same_source_body_produces_host_aware_outputs(self) -> None:
        """O ponto da feature: um body unico apontado pelos 2 targets
        produz outputs diferentes onde o include_per_target esta, e
        outputs identicos no resto."""
        with tempfile.TemporaryDirectory() as tmp:
            mdir, mfile = _sandbox_manifest(
                Path(tmp),
                {
                    "test.md": "SHARED-PROSE.\n\n{{include_per_target: _partials/p}}\n",
                    "_partials/p.agent.md": "A",
                    "_partials/p.claude.md": "C",
                },
                _DUAL_TARGET_MANIFEST,
            )
            outputs = _render_in_sandbox(mdir, mfile, "render_probe_pertarget_shared")
            for output in outputs:
                self.assertIn("SHARED-PROSE.", output.content)
            agent_out = next(o for o in outputs if o.target == "agent_skill")
            claude_out = next(o for o in outputs if o.target == "claude_command")
            self.assertNotEqual(agent_out.content, claude_out.content)

    def test_missing_host_specific_partial_aborts(self) -> None:
        """Se {{include_per_target: foo}} for usado mas o foo.<host>.md
        nao existir para o target sendo renderizado, abortar com a
        mesma mensagem que include normal usa."""
        with tempfile.TemporaryDirectory() as tmp:
            mdir, mfile = _sandbox_manifest(
                Path(tmp),
                {
                    "test.md": "{{include_per_target: _partials/p}}\n",
                    # Apenas claude existe; agent vai faltar.
                    "_partials/p.claude.md": "OK",
                },
                _DUAL_TARGET_MANIFEST,
            )
            module = _load_render_module("render_probe_pertarget_missing")
            paths = _paths_for(module, mdir, mfile)
            try:
                with self.assertRaises(module.RenderError):
                    module.collect_outputs(module.load_manifest(paths), paths)
            finally:
                sys.modules.pop("render_probe_pertarget_missing", None)

    def test_inline_per_target_in_prose_is_left_alone(self) -> None:
        """Mesma garantia do INCLUDE_RE: ancoras ^/$ MULTILINE. Mencao
        em meio de prosa nao dispara substituicao."""
        with tempfile.TemporaryDirectory() as tmp:
            mdir, mfile = _sandbox_manifest(
                Path(tmp),
                {
                    "test.md": "Use `{{include_per_target: foo}}` numa linha sozinha.\n",
                },
                _DUAL_TARGET_MANIFEST,
            )
            outputs = _render_in_sandbox(mdir, mfile, "render_probe_pertarget_prose")
            for output in outputs:
                self.assertIn("{{include_per_target: foo}}", output.content)


class DistInvariantTests(unittest.TestCase):
    """Invariante de saida: nenhum SKILL.md em dist/ deve conter um
    {{include: literal nao expandido. Garante que toda diretiva escrita
    nos bodies foi resolvida no build."""

    def _all_dist_skill_files(self) -> list[Path]:
        candidates: list[Path] = []
        # Agent skills: .agents/skills/<guia-verb>/SKILL.md
        agent_root = DIST / ".agents" / "skills"
        if agent_root.exists():
            candidates.extend(agent_root.rglob("SKILL.md"))
        # Claude commands: commands/<verb>.md (flat)
        cmd_root = DIST / "commands"
        if cmd_root.exists():
            candidates.extend(cmd_root.glob("*.md"))
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
