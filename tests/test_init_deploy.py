"""`/guia:init` full setup: seed .guia/ + deploy lock templates + hooksPath (D-076).

The Claude-plugin consumer gets the engine from the plugin (reached via
`${CLAUDE_PLUGIN_ROOT}`) and only `.guia/` state + lock config in its own
tree. These tests pin the explicit `init` contract:

  1. Seeds `.guia/` AND deploys features/registry.yaml, features/lock-ignore.txt
     and .githooks/commit-msg from the plugin templates dir, then points
     git core.hooksPath at .githooks/.
  2. Idempotent + non-clobbering: a second run preserves edited files.
  3. `--no-locks` seeds `.guia/` only (no lock config, no hook).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CORE_SRC = REPO_ROOT / "core" / "src"
LOCK_API = REPO_ROOT / "core" / "lock" / "lock_api.py"
CHECK_LOCK = REPO_ROOT / "core" / "lock" / "check-lock.py"
TEMPLATES_SRC = REPO_ROOT / "core" / "templates"
HOOK_SRC = REPO_ROOT / "core" / "hooks" / "commit-msg"


def _seed_engine_flat(bin_dir: Path) -> None:
    """Replicate the flat plugin engine layout (plugins/guia/bin/)."""
    bin_dir.mkdir(parents=True)
    for src in CORE_SRC.glob("*.py"):
        if src.name.startswith("__"):
            continue
        shutil.copy2(src, bin_dir / src.name)
    shutil.copy2(LOCK_API, bin_dir / LOCK_API.name)
    shutil.copy2(CHECK_LOCK, bin_dir / CHECK_LOCK.name)


def _seed_templates(plugin_root: Path) -> None:
    """Replicate the shipped templates dir (plugins/guia/templates/)."""
    features = plugin_root / "templates" / "features"
    features.mkdir(parents=True)
    shutil.copy2(TEMPLATES_SRC / "features" / "registry.yaml", features / "registry.yaml")
    shutil.copy2(TEMPLATES_SRC / "features" / "lock-ignore.txt", features / "lock-ignore.txt")
    githooks = plugin_root / "templates" / ".githooks"
    githooks.mkdir(parents=True)
    shutil.copy2(HOOK_SRC, githooks / "commit-msg")


def _git_init(project: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=project, check=True, capture_output=True)


def _run_init(plugin_root: Path, project: Path, *extra: str):
    env = dict(os.environ)
    env["CLAUDE_PLUGIN_ROOT"] = str(plugin_root)
    env.pop("GUIA_PROJECT_ROOT", None)
    return subprocess.run(
        [sys.executable, str(plugin_root / "bin" / "guia.py"), "init", *extra],
        cwd=project,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )


class InitDeployTest(unittest.TestCase):
    def test_full_init_seeds_state_and_deploys_locks(self) -> None:
        with tempfile.TemporaryDirectory() as cache_tmp, tempfile.TemporaryDirectory() as project_tmp:
            plugin_root = Path(cache_tmp) / "plugin"
            _seed_engine_flat(plugin_root / "bin")
            _seed_templates(plugin_root)
            project = Path(project_tmp)
            _git_init(project)

            result = _run_init(plugin_root, project)
            self.assertEqual(result.returncode, 0, msg=f"init falhou: {result.stderr!r}")

            # .guia/ state
            self.assertTrue((project / ".guia" / "process.json").is_file())
            self.assertTrue((project / ".guia" / "tasks.json").is_file())
            # lock config + hook deployed from the plugin templates
            self.assertTrue((project / "features" / "registry.yaml").is_file())
            self.assertTrue((project / "features" / "lock-ignore.txt").is_file())
            self.assertTrue((project / ".githooks" / "commit-msg").is_file())
            # engine code does NOT land in the consumer (plugin-global)
            self.assertFalse((project / "bin").exists())
            self.assertFalse((project / "core").exists())

            # hooksPath configured
            cfg = subprocess.run(
                ["git", "config", "--local", "core.hooksPath"],
                cwd=project, capture_output=True, text=True,
            )
            self.assertEqual(cfg.stdout.strip(), ".githooks")

    def test_idempotent_does_not_clobber_edits(self) -> None:
        with tempfile.TemporaryDirectory() as cache_tmp, tempfile.TemporaryDirectory() as project_tmp:
            plugin_root = Path(cache_tmp) / "plugin"
            _seed_engine_flat(plugin_root / "bin")
            _seed_templates(plugin_root)
            project = Path(project_tmp)
            _git_init(project)

            self.assertEqual(_run_init(plugin_root, project).returncode, 0)
            # Developer customizes the registry afterwards.
            registry = project / "features" / "registry.yaml"
            registry.write_text("version: 1\nlocks: []\n# custom\n", encoding="utf-8")

            self.assertEqual(_run_init(plugin_root, project).returncode, 0)
            self.assertIn(
                "# custom",
                registry.read_text(encoding="utf-8"),
                "init clobbered an existing registry.yaml (must be no-clobber)",
            )

    def test_no_locks_seeds_state_only(self) -> None:
        with tempfile.TemporaryDirectory() as cache_tmp, tempfile.TemporaryDirectory() as project_tmp:
            plugin_root = Path(cache_tmp) / "plugin"
            _seed_engine_flat(plugin_root / "bin")
            _seed_templates(plugin_root)
            project = Path(project_tmp)
            _git_init(project)

            result = _run_init(plugin_root, project, "--no-locks")
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            self.assertTrue((project / ".guia" / "process.json").is_file())
            self.assertFalse((project / "features").exists())
            self.assertFalse((project / ".githooks").exists())


if __name__ == "__main__":
    unittest.main()
