"""D-047: testes de composicao real dos bodies via partials.

Diferente de test_render_includes (que testa o mecanismo), aqui testa
o RESULTADO: os arquivos gerados em plugins/guia/ (commands/ do Claude e
.agents/skills/ do agente) tem o conteudo esperado de cada partial nos
verbos certos, e nao nos verbos errados.

Mapa de inclusao (intent design):
    title_context_rules.md → feature, bug, chore, backlog
    lock_protocol.md       → feature, bug, chore, promote, finish
    post_cli.<host>.md     → todos os 7 verbos shim (ja que
                             "ler current-task + repetir NOME DA DEMANDA
                             + rename opcional do chat" e universal pos-CLI)
    nada em ready -> sem lock_protocol (ready nao edita arquivos)
    nada em backlog -> sem lock_protocol (backlog parqueia, nao edita)

Tambem garante que partials existem e que o README esta presente.
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from conftest_paths import REPO_ROOT

RENDER = REPO_ROOT / "core" / "build" / "render-skills.py"
PARTIALS = REPO_ROOT / "core" / "manifest" / "bodies" / "_partials"
CLAUDE_COMMANDS = REPO_ROOT / "plugins" / "guia" / "commands"
AGENT_DIST = REPO_ROOT / "plugins" / "guia" / ".agents" / "skills"


# Marcadores estaveis dentro de cada partial - se alguem reescrever um
# partial, esses headings precisam aparecer (caso contrario o teste
# acusa que a composicao nao incluiu o partial certo).
TITLE_CONTEXT_MARKER = "## Title vs Context"
LOCK_PROTOCOL_MARKER = "## File locks"
POST_CLI_MARKER = "## After running the script"
CLAUDE_RENAME_MARKER = "mark_chapter"
AGENT_RENAME_MARKER = "codex_app.set_thread_title"


def _claude_command(verb: str) -> Path:
    return CLAUDE_COMMANDS / f"{verb}.md"


def _agent_skill(verb: str) -> Path:
    return AGENT_DIST / f"guia-{verb}" / "SKILL.md"


def _ensure_dist_in_sync() -> None:
    """Renderer --check passa antes de ler dist/. Se falhar, o teste e
    inconclusivo - melhor abortar com mensagem clara do que afirmar
    contra um dist/ stale."""
    result = subprocess.run(
        [sys.executable, str(RENDER), "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"dist/ esta stale antes do teste de body_partials.\n"
            f"Rode: python core/build/render-skills.py\n\n"
            f"stderr: {result.stderr}"
        )


class PartialFilesExistTests(unittest.TestCase):
    def test_partials_directory_exists(self) -> None:
        self.assertTrue(PARTIALS.is_dir(), msg=f"{PARTIALS} ausente")

    def test_readme_present(self) -> None:
        self.assertTrue((PARTIALS / "README.md").is_file())

    def test_expected_partials_exist(self) -> None:
        expected = {
            "title_context_rules.md",
            "lock_protocol.md",
            "post_cli.agent.md",
            "post_cli.claude.md",
            "run_cmd.agent.md",
            "run_cmd.claude.md",
        }
        actual = {p.name for p in PARTIALS.glob("*.md") if p.name != "README.md"}
        self.assertEqual(
            actual,
            expected,
            msg=f"partials esperados {expected}, encontrados {actual}",
        )


class TitleContextCompositionTests(unittest.TestCase):
    """title_context_rules.md deve aparecer nos verbos que criam tasks
    (feature/bug/chore/backlog), e NAO nos verbos de lifecycle
    (promote/ready/finish/status)."""

    @classmethod
    def setUpClass(cls) -> None:
        _ensure_dist_in_sync()

    def test_create_verbs_have_title_context(self) -> None:
        for verb in ("feature", "bug", "chore", "backlog"):
            for skill_path in (_claude_command(verb), _agent_skill(verb)):
                text = skill_path.read_text(encoding="utf-8")
                self.assertIn(
                    TITLE_CONTEXT_MARKER,
                    text,
                    msg=f"{skill_path.relative_to(REPO_ROOT)} sem '{TITLE_CONTEXT_MARKER}'",
                )

    def test_lifecycle_verbs_do_not_have_title_context(self) -> None:
        for verb in ("promote", "ready", "finish"):
            for skill_path in (_claude_command(verb), _agent_skill(verb)):
                text = skill_path.read_text(encoding="utf-8")
                self.assertNotIn(
                    TITLE_CONTEXT_MARKER,
                    text,
                    msg=f"{skill_path.relative_to(REPO_ROOT)} nao deveria ter '{TITLE_CONTEXT_MARKER}'",
                )


class LockProtocolCompositionTests(unittest.TestCase):
    """lock_protocol.md deve aparecer em qualquer verbo que edita
    arquivos: feature, bug, chore (criadores que vao implementar),
    promote (executa plano), finish (pode trancar). NAO em backlog
    (parqueia), ready (handoff), status (read-only)."""

    @classmethod
    def setUpClass(cls) -> None:
        _ensure_dist_in_sync()

    def test_editing_verbs_have_lock_protocol(self) -> None:
        for verb in ("feature", "bug", "chore", "promote", "finish"):
            for skill_path in (_claude_command(verb), _agent_skill(verb)):
                text = skill_path.read_text(encoding="utf-8")
                self.assertIn(
                    LOCK_PROTOCOL_MARKER,
                    text,
                    msg=f"{skill_path.relative_to(REPO_ROOT)} sem '{LOCK_PROTOCOL_MARKER}'",
                )

    def test_non_editing_verbs_lack_lock_protocol(self) -> None:
        for verb in ("backlog", "ready"):
            for skill_path in (_claude_command(verb), _agent_skill(verb)):
                text = skill_path.read_text(encoding="utf-8")
                self.assertNotIn(
                    LOCK_PROTOCOL_MARKER,
                    text,
                    msg=f"{skill_path.relative_to(REPO_ROOT)} nao deveria ter '{LOCK_PROTOCOL_MARKER}'",
                )


class PostCliCompositionTests(unittest.TestCase):
    """post_cli.<host>.md deve aparecer em todos os 7 verbos shim. E o
    host certo: mark_chapter so no claude command, codex_app so na
    agent skill (cross-contaminacao seria bug grave)."""

    @classmethod
    def setUpClass(cls) -> None:
        _ensure_dist_in_sync()

    VERBS = ("feature", "bug", "chore", "backlog", "promote", "ready", "finish")

    def test_all_verbs_have_post_cli(self) -> None:
        for verb in self.VERBS:
            for skill_path in (_claude_command(verb), _agent_skill(verb)):
                text = skill_path.read_text(encoding="utf-8")
                self.assertIn(
                    POST_CLI_MARKER,
                    text,
                    msg=f"{skill_path.relative_to(REPO_ROOT)} sem '{POST_CLI_MARKER}'",
                )

    def test_claude_targets_use_mark_chapter(self) -> None:
        for verb in self.VERBS:
            text = _claude_command(verb).read_text(encoding="utf-8")
            self.assertIn(
                CLAUDE_RENAME_MARKER,
                text,
                msg=f"{_claude_command(verb).relative_to(REPO_ROOT)} sem '{CLAUDE_RENAME_MARKER}'",
            )

    def test_agent_targets_use_codex_app(self) -> None:
        for verb in self.VERBS:
            text = _agent_skill(verb).read_text(encoding="utf-8")
            self.assertIn(
                AGENT_RENAME_MARKER,
                text,
                msg=f"{_agent_skill(verb).relative_to(REPO_ROOT)} sem '{AGENT_RENAME_MARKER}'",
            )

    def test_no_cross_contamination_between_hosts(self) -> None:
        """claude SKILL.md nao deve mencionar codex_app; agent SKILL.md
        nao deve mencionar mark_chapter. Caso contrario um partial foi
        incluido no host errado em algum body."""
        for verb in self.VERBS:
            claude_text = _claude_command(verb).read_text(encoding="utf-8")
            agent_text = _agent_skill(verb).read_text(encoding="utf-8")
            self.assertNotIn(
                AGENT_RENAME_MARKER,
                claude_text,
                msg=f"{_claude_command(verb).relative_to(REPO_ROOT)} contaminado com instrucao Codex App",
            )
            self.assertNotIn(
                CLAUDE_RENAME_MARKER,
                agent_text,
                msg=f"{_agent_skill(verb).relative_to(REPO_ROOT)} contaminado com instrucao mark_chapter (Claude)",
            )


class FrontmatterAndTitleTests(unittest.TestCase):
    """Garantias do frontmatter dos arquivos gerados:
    - Comecam com `---`.
    - Claude target = plugin *command* `commands/<verb>.md`: SEM `name:` no
      frontmatter (o nome vem do stem do arquivo -> surge como `/guia:<verb>`).
    - Agent target = Agent Skill `guia-<verb>/SKILL.md`: COM `name: guia-<verbo>`.
    - Tem `description:` nao vazia em ambos.
    """

    @classmethod
    def setUpClass(cls) -> None:
        _ensure_dist_in_sync()

    VERBS = ("feature", "bug", "chore", "backlog", "promote", "ready", "finish", "status")

    def test_claude_command_file_per_verb_without_name(self) -> None:
        for verb in self.VERBS:
            path = _claude_command(verb)
            if not path.exists():
                continue  # `status` pode nao estar listado em todos os layouts
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), msg=f"{path} sem frontmatter")
            # Command flat: o nome vem do stem do arquivo (<verb>.md), entao
            # NAO deve haver `name:` no frontmatter (senao surgiria duplicado).
            head = text.split("\n---\n", 1)[0]
            self.assertNotIn(
                "\nname:", head, msg=f"{path} nao deveria ter `name:` (command usa o stem)"
            )

    def test_agent_skill_name_has_guia_prefix(self) -> None:
        for verb in self.VERBS:
            path = _agent_skill(verb)
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), msg=f"{path} sem frontmatter")
            self.assertIn(
                f"\nname: guia-{verb}\n",
                text,
                msg=f"{path} sem `name: guia-{verb}`",
            )

    def test_description_present_and_nonempty(self) -> None:
        for verb in self.VERBS:
            for path in (_claude_command(verb), _agent_skill(verb)):
                if not path.exists():
                    continue
                text = path.read_text(encoding="utf-8")
                # Procura "description: " no frontmatter (entre os dois `---`).
                head = text.split("\n---\n", 1)[0]
                desc_lines = [ln for ln in head.splitlines() if ln.startswith("description: ")]
                self.assertEqual(
                    len(desc_lines),
                    1,
                    msg=f"{path} deveria ter exatamente uma linha 'description: '",
                )
                self.assertGreater(
                    len(desc_lines[0]),
                    len("description: "),
                    msg=f"{path} com description vazio",
                )


if __name__ == "__main__":
    unittest.main()
