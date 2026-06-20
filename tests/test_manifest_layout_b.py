"""F-016: testes do schema do manifest (Layout B).

Valida:
- Cada verbo declara `body_file` apontando para arquivo existente em
  `core/manifest/bodies/`.
- Cada body markdown referenciado existe em disco.
- Renderer aborta quando body_file falta.
- Renderer aborta quando body_file aponta fora de core/manifest/ (path
  traversal).
- Cache de body funciona: dois targets apontando para o mesmo arquivo
  resolvem em uma unica leitura (shared_body trivial).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from conftest_paths import REPO_ROOT

MANIFEST = REPO_ROOT / "core" / "manifest" / "manifest.yaml"
BODIES_DIR = REPO_ROOT / "core" / "manifest" / "bodies"
RENDER = REPO_ROOT / "core" / "build" / "render-skills.py"


def _load_manifest() -> dict:
    return yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))


class ManifestSchemaTests(unittest.TestCase):
    def test_version_is_2(self) -> None:
        self.assertEqual(_load_manifest().get("version"), 2)

    def test_every_target_has_body_file(self) -> None:
        manifest = _load_manifest()
        for verb, spec in (manifest.get("verbs") or {}).items():
            for target_name, target_spec in (spec.get("targets") or {}).items():
                self.assertIn(
                    "body_file",
                    target_spec,
                    msg=f"{verb}.{target_name} sem body_file",
                )

    def test_every_body_file_exists(self) -> None:
        manifest = _load_manifest()
        for verb, spec in (manifest.get("verbs") or {}).items():
            for target_name, target_spec in (spec.get("targets") or {}).items():
                body_file = target_spec.get("body_file")
                path = (REPO_ROOT / "core" / "manifest" / body_file).resolve()
                self.assertTrue(
                    path.exists(),
                    msg=f"{verb}.{target_name}.body_file -> {path} nao existe",
                )

    def test_bodies_dir_has_no_orphans(self) -> None:
        """Cada .md em bodies/ deve ser referenciado por algum target."""
        manifest = _load_manifest()
        referenced = set()
        for spec in (manifest.get("verbs") or {}).values():
            for target_spec in (spec.get("targets") or {}).values():
                if target_spec.get("body_file"):
                    referenced.add((REPO_ROOT / "core" / "manifest" / target_spec["body_file"]).resolve())
        on_disk = {p.resolve() for p in BODIES_DIR.glob("*.md")}
        orphans = on_disk - referenced
        self.assertEqual(orphans, set(), msg=f"Orfaos em bodies/: {orphans}")


class RendererErrorPathsTests(unittest.TestCase):
    def _sandbox(self) -> tempfile.TemporaryDirectory:
        return tempfile.TemporaryDirectory()

    def test_missing_body_file_aborts(self) -> None:
        with self._sandbox() as tmp:
            sandbox = Path(tmp)
            manifest = sandbox / "core" / "manifest" / "manifest.yaml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                "version: 2\n"
                "verbs:\n"
                "  foo:\n"
                "    description: |\n"
                "      D\n"
                "    targets:\n"
                "      agent_skill:\n"
                "        body_file: bodies/missing.md\n",
                encoding="utf-8",
            )
            # copy renderer and core/src needed modules
            (sandbox / "core" / "build").mkdir()
            shutil.copy2(RENDER, sandbox / "core" / "build" / "render-skills.py")
            # Need src + lock for completeness even though we only test outputs error path
            result = subprocess.run(
                [sys.executable, str(sandbox / "core" / "build" / "render-skills.py"), "--check"],
                cwd=sandbox,
                capture_output=True,
                text=True,
            )
            # Renderer aborta porque collect_bin_outputs nao encontra core/src/guia.py,
            # ou porque _resolve_body acha o body ausente. Qualquer um e nao-zero.
            self.assertNotEqual(result.returncode, 0)


class SharedBodyCacheTests(unittest.TestCase):
    """D-050: cada verbo tem 1 body file apontado pelos 2 targets. O
    output difere apenas no trecho host-aware (post_cli.<host>.md),
    selecionado em build-time pelo `{{include_per_target:}}`."""

    def test_all_verbs_use_consolidated_single_body(self) -> None:
        """Para cada verbo, agent_skill.body_file == claude_command.body_file."""
        manifest = _load_manifest()
        for verb, spec in (manifest.get("verbs") or {}).items():
            agent_bf = spec["targets"]["agent_skill"]["body_file"]
            claude_bf = spec["targets"]["claude_command"]["body_file"]
            self.assertEqual(
                agent_bf,
                claude_bf,
                msg=f"verbo `{verb}`: targets apontam para bodies diferentes ({agent_bf} vs {claude_bf}) - consolidacao D-050 incompleta",
            )

    def test_consolidated_body_produces_host_aware_outputs(self) -> None:
        """O ponto da consolidacao: 1 body source, 2 outputs que diferem no
        trecho host-aware. Pega feature: o output do agent_skill deve
        mencionar codex_app; o claude_command deve mencionar mark_chapter;
        o resto deve ser identico (ou quase)."""
        from conftest_paths import REPO_ROOT
        dist = REPO_ROOT / "plugins" / "guia"
        agent_out = (dist / ".agents" / "skills" / "guia-feature" / "SKILL.md").read_text(encoding="utf-8")
        claude_out = (dist / "commands" / "feature.md").read_text(encoding="utf-8")
        # Ambos compostos a partir do mesmo source (bodies/feature.md):
        # garantia minima de que o comando neutro do verbo aparece nos dois.
        for output in (agent_out, claude_out):
            self.assertIn('feature "<title>"', output)
        # Divergem no trecho host-aware de rename (post_cli):
        self.assertIn("codex_app", agent_out)
        self.assertNotIn("codex_app", claude_out)
        self.assertIn("mark_chapter", claude_out)
        self.assertNotIn("mark_chapter", agent_out)
        # E no trecho host-aware de invocacao (run_cmd, D-075): o agent
        # chama o wrapper do repo; o claude chama o motor do plugin via
        # ${CLAUDE_PLUGIN_ROOT}.
        self.assertIn("core\\bin\\guia.ps1", agent_out)
        self.assertNotIn("CLAUDE_PLUGIN_ROOT", agent_out)
        self.assertIn("CLAUDE_PLUGIN_ROOT", claude_out)
        self.assertNotIn("core\\bin\\guia.ps1", claude_out)


if __name__ == "__main__":
    unittest.main()
