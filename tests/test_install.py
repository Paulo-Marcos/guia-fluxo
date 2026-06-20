"""Smoke test do instalador: simula install em tempdir e valida layout consumer.

Independente de install.ps1 / install.sh para rodar cross-platform na CI -
replica o mapa de copia em Python puro e roda `ai doctor` do .guia-fluxo/bin/
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
DIST = REPO_ROOT / "plugins" / "guia"


# Origem (dentro de plugins/guia/) -> destino relativo ao consumer.
PLUGIN_COPIES = [
    (".claude-plugin", ".guia-fluxo/.claude-plugin"),
    ("commands", ".guia-fluxo/commands"),
    ("bin", ".guia-fluxo/bin"),
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

    # ai init para semear .guia/ e FEATURES.md.
    subprocess.run(
        [sys.executable, str(target / ".guia-fluxo/bin/guia.py"), "init",
         "--project-name", "smoke-install"],
        cwd=target, check=True, capture_output=True, text=True,
    )


class InstallSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        if not DIST.exists():
            self.skipTest("plugins/guia/ ausente - rode 'python core/build/render-skills.py' antes")

    def test_layout_consumidor(self) -> None:
        """Apos install, layout esperado deve existir e doctor passar."""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            install_into(target)

            # Plugin no .guia-fluxo/
            self.assertTrue((target / ".guia-fluxo/.claude-plugin/plugin.json").is_file())
            self.assertTrue((target / ".guia-fluxo/commands/feature.md").is_file())
            self.assertTrue((target / ".guia-fluxo/bin/guia.py").is_file())
            self.assertTrue((target / ".guia-fluxo/bin/guia.ps1").is_file())
            self.assertTrue((target / ".guia-fluxo/bin/guia").is_file())

            # Cross-tool com prefixo guia-
            self.assertTrue((target / ".agents/skills/guia-feature/SKILL.md").is_file())
            self.assertTrue((target / ".agents/skills/guia-fluxo/SKILL.md").is_file())
            self.assertFalse((target / ".agents/skills/feature/SKILL.md").exists(),
                             "skills sem prefixo nao devem aparecer no .agents/skills/")

            # Templates (devem aparecer no primeiro install)
            self.assertTrue((target / ".githooks/commit-msg").is_file())
            self.assertTrue((target / "features/registry.yaml").is_file())
            self.assertTrue((target / "features/lock-ignore.txt").is_file())

            # Estado do .guia/ semeado por ai init
            # FEATURES.md nao e criado por init - so pelo primeiro feature/issue,
            # entao nao validamos aqui.
            self.assertTrue((target / ".guia/process.json").is_file())
            self.assertTrue((target / ".guia/tasks.json").is_file())
            self.assertTrue((target / ".guia/backlog.json").is_file())

            # Frontmatter prefixado no cross-tool
            head = (target / ".agents/skills/guia-feature/SKILL.md").read_text(encoding="utf-8")
            self.assertIn("name: guia-feature", head)
            head_process = (target / ".agents/skills/guia-fluxo/SKILL.md").read_text(encoding="utf-8")
            self.assertIn("name: guia-fluxo", head_process)  # sem duplo prefixo

            # Doctor passa rodando o motor standalone do consumer
            result = subprocess.run(
                [sys.executable, str(target / ".guia-fluxo/bin/guia.py"), "doctor"],
                cwd=target, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0,
                             msg=f"doctor falhou: stdout={result.stdout!r} stderr={result.stderr!r}")
            self.assertIn("Guia Fluxo files OK", result.stdout)

    def test_shim_posix_e_lf(self) -> None:
        """plugins/guia/bin/guia (shim bash) precisa de LF puro para Linux/Mac."""
        shim = (DIST / "bin/guia").read_bytes()
        self.assertNotIn(b"\r\n", shim,
                         "shim POSIX plugins/guia/bin/guia contem CRLF - bash quebra em Linux/Mac")

    def test_wrapper_ps1_aponta_para_guia_py_local(self) -> None:
        """plugins/guia/bin/guia.ps1 deve resolver guia.py na mesma pasta (layout
        flat), nao via ..\\src\\guia.py que so existe no repo-mae."""
        wrapper = (DIST / "bin/guia.ps1").read_text(encoding="utf-8")
        self.assertIn('Join-Path $PSScriptRoot "guia.py"', wrapper)
        self.assertNotIn("..\\src\\guia.py", wrapper)


if __name__ == "__main__":
    unittest.main()
