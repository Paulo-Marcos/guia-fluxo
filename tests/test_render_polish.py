"""F-019: tests para --clean, --output-dir, frontmatter extras, shared_body."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from conftest_paths import REPO_ROOT

RENDER = REPO_ROOT / "core" / "build" / "render-skills.py"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RENDER), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


class OutputDirTests(unittest.TestCase):
    def test_output_dir_writes_to_custom_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            result = _run("--output-dir", str(out))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            # Pelo menos 1 SKILL.md + ai.py em bin/
            self.assertTrue((out / "bin" / "ai.py").is_file())
            self.assertTrue((out / "skills" / "feature" / "SKILL.md").is_file())
            self.assertTrue((out / ".agents" / "skills" / "ai-feature" / "SKILL.md").is_file())

    def test_check_with_custom_output_dir_compares_against_that_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            # Primeiro write
            _run("--output-dir", str(out))
            # Agora --check deve passar
            result = _run("--check", "--output-dir", str(out))
            self.assertEqual(result.returncode, 0, msg=result.stderr)


class CleanTests(unittest.TestCase):
    def test_clean_removes_orphan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            _run("--output-dir", str(out))
            # Plantar um orfao
            orphan_dir = out / "skills" / "verbo-fantasma"
            orphan_dir.mkdir(parents=True)
            (orphan_dir / "SKILL.md").write_text("fantasma", encoding="utf-8")
            # --clean deve apagar
            result = _run("--clean", "--output-dir", str(out))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertFalse((orphan_dir / "SKILL.md").exists())
            # Diretorio vazio tambem deve sumir
            self.assertFalse(orphan_dir.exists())


class FrontmatterExtrasTests(unittest.TestCase):
    """Testa que `frontmatter:` no verbo vira linhas extras no SKILL.md."""

    def _sandbox_manifest(self, sandbox: Path) -> None:
        """Setup minimo: manifest + 1 body + render-skills.py copiado.
        Mas usa o manifest real do repo via --output-dir em vez de
        sandbox completo (renderer depende de core/src/ai.py, etc.)."""
        pass  # nao usado; teste roda contra repo real

    def test_extras_appear_in_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            # Manifest temporario com frontmatter extra
            tmp_manifest_dir = Path(tmp) / "manifest"
            tmp_manifest_dir.mkdir()
            tmp_bodies = tmp_manifest_dir / "bodies"
            tmp_bodies.mkdir()
            (tmp_bodies / "test.claude.md").write_text("# Test\n\nBody.\n", encoding="utf-8")
            tmp_manifest = tmp_manifest_dir / "manifest.yaml"
            tmp_manifest.write_text(
                "version: 2\n"
                "verbs:\n"
                "  test:\n"
                "    description: |\n"
                "      Test description.\n"
                "    frontmatter:\n"
                "      allowed-tools: [Read, Edit]\n"
                "      model: opus\n"
                "    targets:\n"
                "      claude_skill:\n"
                "        body_file: bodies/test.claude.md\n",
                encoding="utf-8",
            )
            # Carrega manifest direto sem rodar o CLI (que esperaria
            # core/src/ai.py existir relativo a um repo)
            from conftest_paths import ensure_core_importable

            ensure_core_importable()
            import importlib

            # Recarrega o render-skills com MANIFEST patched
            spec = importlib.util.spec_from_file_location("render_skills_probe", RENDER)
            module = importlib.util.module_from_spec(spec)
            sys.modules["render_skills_probe"] = module
            try:
                spec.loader.exec_module(module)
                module.MANIFEST_DIR = tmp_manifest_dir
                module.MANIFEST = tmp_manifest
                manifest_data = module.load_manifest()
                outputs = module.collect_outputs(manifest_data)
                test_output = next(o for o in outputs if o.name == "test" and o.target == "claude_skill")
                content = test_output.content
                self.assertIn("allowed-tools: [Read, Edit]", content)
                self.assertIn("model: opus", content)
                self.assertIn("name: test", content)
                self.assertIn("description: Test description.", content)
            finally:
                sys.modules.pop("render_skills_probe", None)


class SharedBodyExplicitTests(unittest.TestCase):
    """`shared_body:` no verbo aplica a TODOS targets sem body_file."""

    def test_shared_body_applies_to_all_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_manifest_dir = Path(tmp) / "manifest"
            (tmp_manifest_dir / "bodies").mkdir(parents=True)
            (tmp_manifest_dir / "bodies" / "shared.md").write_text("# Shared\n", encoding="utf-8")
            tmp_manifest = tmp_manifest_dir / "manifest.yaml"
            tmp_manifest.write_text(
                "version: 2\n"
                "verbs:\n"
                "  test:\n"
                "    description: |\n"
                "      Test description.\n"
                "    shared_body: bodies/shared.md\n"
                "    targets:\n"
                "      agent_skill: {}\n"
                "      claude_skill: {}\n",
                encoding="utf-8",
            )
            from conftest_paths import ensure_core_importable

            ensure_core_importable()
            import importlib

            spec = importlib.util.spec_from_file_location("render_skills_probe2", RENDER)
            module = importlib.util.module_from_spec(spec)
            sys.modules["render_skills_probe2"] = module
            try:
                spec.loader.exec_module(module)
                module.MANIFEST_DIR = tmp_manifest_dir
                module.MANIFEST = tmp_manifest
                manifest_data = module.load_manifest()
                outputs = module.collect_outputs(manifest_data)
                # 2 outputs (agent + claude) ambos com `# Shared` no corpo
                self.assertEqual(len(outputs), 2)
                for output in outputs:
                    self.assertIn("# Shared", output.content)
            finally:
                sys.modules.pop("render_skills_probe2", None)

    def test_target_body_file_overrides_shared(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_manifest_dir = Path(tmp) / "manifest"
            (tmp_manifest_dir / "bodies").mkdir(parents=True)
            (tmp_manifest_dir / "bodies" / "shared.md").write_text("# Shared\n", encoding="utf-8")
            (tmp_manifest_dir / "bodies" / "specific.md").write_text("# Specific\n", encoding="utf-8")
            tmp_manifest = tmp_manifest_dir / "manifest.yaml"
            tmp_manifest.write_text(
                "version: 2\n"
                "verbs:\n"
                "  test:\n"
                "    description: |\n"
                "      Test description.\n"
                "    shared_body: bodies/shared.md\n"
                "    targets:\n"
                "      agent_skill: {}\n"
                "      claude_skill:\n"
                "        body_file: bodies/specific.md\n",
                encoding="utf-8",
            )
            from conftest_paths import ensure_core_importable

            ensure_core_importable()
            import importlib

            spec = importlib.util.spec_from_file_location("render_skills_probe3", RENDER)
            module = importlib.util.module_from_spec(spec)
            sys.modules["render_skills_probe3"] = module
            try:
                spec.loader.exec_module(module)
                module.MANIFEST_DIR = tmp_manifest_dir
                module.MANIFEST = tmp_manifest
                outputs = module.collect_outputs(module.load_manifest())
                agent_out = next(o for o in outputs if o.target == "agent_skill")
                claude_out = next(o for o in outputs if o.target == "claude_skill")
                self.assertIn("# Shared", agent_out.content)
                self.assertIn("# Specific", claude_out.content)
                self.assertNotIn("# Shared", claude_out.content)
            finally:
                sys.modules.pop("render_skills_probe3", None)


if __name__ == "__main__":
    unittest.main()
