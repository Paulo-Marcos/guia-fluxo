"""Smoke test do instalador: simula install em tempdir e valida layout consumer.

Independente de install.ps1 / install.sh para rodar cross-platform na CI -
replica o mapa de copia em Python puro e roda `ai doctor` do .ai-process/bin/
no tempdir. Se este teste passar, os dois scripts (que sao paridade) podem
ser confiados.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DIST = REPO_ROOT / "dist"


# Origem (dentro de dist/) -> destino relativo ao consumer.
PLUGIN_COPIES = [
    (".claude-plugin", ".ai-process/.claude-plugin"),
    ("skills", ".ai-process/skills"),
    ("bin", ".ai-process/bin"),
    (".agents/skills", ".agents/skills"),
]

TEMPLATE_COPIES = [
    ("templates/.githooks/commit-msg", ".githooks/commit-msg"),
    ("templates/features/registry.yaml", "features/registry.yaml"),
    ("templates/features/lock-ignore.txt", "features/lock-ignore.txt"),
]


def install_into(target: Path) -> None:
    """Replica logica de install.ps1/install.sh em Python para o teste."""
    for src_rel, dst_rel in PLUGIN_COPIES:
        src = DIST / src_rel
        dst = target / dst_rel
        if dst.exists():
            shutil.rmtree(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst)

    for src_rel, dst_rel in TEMPLATE_COPIES:
        src = DIST / src_rel
        dst = target / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    # ai init para semear .ai/ e FEATURES.md.
    subprocess.run(
        [sys.executable, str(target / ".ai-process/bin/ai.py"), "init",
         "--project-name", "smoke-install"],
        cwd=target, check=True, capture_output=True, text=True,
    )


class InstallSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        if not DIST.exists():
            self.skipTest("dist/ ausente - rode 'python core/build/render-skills.py' antes")

    def test_layout_consumidor(self) -> None:
        """Apos install, layout esperado deve existir e doctor passar."""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            install_into(target)

            # Plugin no .ai-process/
            self.assertTrue((target / ".ai-process/.claude-plugin/plugin.json").is_file())
            self.assertTrue((target / ".ai-process/skills/feature/SKILL.md").is_file())
            self.assertTrue((target / ".ai-process/bin/ai.py").is_file())
            self.assertTrue((target / ".ai-process/bin/ai.ps1").is_file())
            self.assertTrue((target / ".ai-process/bin/ai").is_file())

            # Cross-tool com prefixo ai-
            self.assertTrue((target / ".agents/skills/ai-feature/SKILL.md").is_file())
            self.assertTrue((target / ".agents/skills/ai-process/SKILL.md").is_file())
            self.assertFalse((target / ".agents/skills/feature/SKILL.md").exists(),
                             "skills sem prefixo nao devem aparecer no .agents/skills/")

            # Templates (devem aparecer no primeiro install)
            self.assertTrue((target / ".githooks/commit-msg").is_file())
            self.assertTrue((target / "features/registry.yaml").is_file())
            self.assertTrue((target / "features/lock-ignore.txt").is_file())

            # Estado do .ai/ semeado por ai init
            # FEATURES.md nao e criado por init - so pelo primeiro feature/issue,
            # entao nao validamos aqui.
            self.assertTrue((target / ".ai/process.json").is_file())
            self.assertTrue((target / ".ai/tasks.json").is_file())
            self.assertTrue((target / ".ai/backlog.json").is_file())

            # Frontmatter prefixado no cross-tool
            head = (target / ".agents/skills/ai-feature/SKILL.md").read_text(encoding="utf-8")
            self.assertIn("name: ai-feature", head)
            head_process = (target / ".agents/skills/ai-process/SKILL.md").read_text(encoding="utf-8")
            self.assertIn("name: ai-process", head_process)  # sem duplo prefixo

            # Doctor passa rodando o motor standalone do consumer
            result = subprocess.run(
                [sys.executable, str(target / ".ai-process/bin/ai.py"), "doctor"],
                cwd=target, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0,
                             msg=f"doctor falhou: stdout={result.stdout!r} stderr={result.stderr!r}")
            self.assertIn("AI process files OK", result.stdout)

    def test_shim_posix_e_lf(self) -> None:
        """dist/bin/ai (shim bash) precisa de LF puro para rodar em Linux/Mac."""
        shim = (DIST / "bin/ai").read_bytes()
        self.assertNotIn(b"\r\n", shim,
                         "shim POSIX dist/bin/ai contem CRLF - bash quebra em Linux/Mac")

    def test_wrapper_ps1_aponta_para_ai_py_local(self) -> None:
        """dist/bin/ai.ps1 deve resolver ai.py na mesma pasta (layout flat),
        nao via ..\\src\\ai.py que so existe no repo-mae."""
        wrapper = (DIST / "bin/ai.ps1").read_text(encoding="utf-8")
        self.assertIn('Join-Path $PSScriptRoot "ai.py"', wrapper)
        self.assertNotIn("..\\src\\ai.py", wrapper)


if __name__ == "__main__":
    unittest.main()
