"""D-054 (absorve B-019): montagem da mensagem de commit enriquecida.

`build_commit_message` e a funcao pura por tras de `commit_task`: monta o texto
do commit a partir da task, sem tocar em git. Estes testes fixam o contrato:

- header em Conventional Commits com o id da task como scope: `{kind}({id}): {title}`;
- corpo legivel com summary (o que foi feito), validacoes e arquivos;
- rodape `Task: {id}` LITERAL e por ultimo (ancora estavel para parsers);
- complemento manual via `--commit-body`;
- blocos vazios sao omitidos (mensagem previsivel quando os campos faltam).
"""

from __future__ import annotations

import unittest

from conftest_paths import ensure_core_importable

ensure_core_importable()

import _commit  # noqa: E402
from _constants import MSG_NONE_PLACEHOLDER  # noqa: E402


def _task(**over: object) -> dict:
    base = {
        "id": "D-054",
        "kind": "feature",
        "title": "Enriquecer mensagem de commit com resumo do que foi feito",
        "summary": ["Inclui summary, validacoes e arquivos no corpo do commit."],
        "validations": ["python -m pytest tests/test_commit_message.py"],
        "modifiedFiles": ["core/src/_commit.py", "core/src/guia.py"],
    }
    base.update(over)
    return base


class HeaderTests(unittest.TestCase):
    def test_header_is_conventional_commit_with_id_as_scope(self) -> None:
        msg = _commit.build_commit_message(_task())
        self.assertTrue(
            msg.startswith(
                "feature(D-054): Enriquecer mensagem de commit com resumo do que foi feito\n\n"
            ),
            msg,
        )

    def test_kind_word_is_preserved_not_remapped_to_feat(self) -> None:
        # A convencao do repo usa `feature:`/`bug:`/`chore:`, nao `feat`/`fix`.
        self.assertTrue(
            _commit.build_commit_message(_task(kind="bug")).startswith("bug(D-054):")
        )


class BodyTests(unittest.TestCase):
    def test_body_contains_summary_validations_and_files(self) -> None:
        msg = _commit.build_commit_message(_task())
        self.assertIn("- Inclui summary, validacoes e arquivos no corpo do commit.", msg)
        self.assertIn("Validacoes:", msg)
        self.assertIn("- python -m pytest tests/test_commit_message.py", msg)
        self.assertIn("Arquivos:", msg)
        self.assertIn("- core/src/_commit.py", msg)
        self.assertIn("- core/src/guia.py", msg)

    def test_task_footer_is_last_line_and_literal(self) -> None:
        # Ancora estavel para parsers existentes: deve permanecer `Task: {id}`.
        msg = _commit.build_commit_message(_task())
        self.assertTrue(msg.endswith("\n\nTask: D-054"), msg)

    def test_commit_body_is_appended_before_footer(self) -> None:
        msg = _commit.build_commit_message(_task(), commit_body="Detalhe manual extra.")
        self.assertIn("Detalhe manual extra.", msg)
        # Complemento manual vem antes do rodape Task:.
        self.assertLess(msg.index("Detalhe manual extra."), msg.index("Task: D-054"))


class SubjectOverrideTests(unittest.TestCase):
    """Ajuste D-054: a skill de convencao do usuario gera o subject; o engine o
    usa no lugar do header padrao, mas preserva corpo e rodape Task:."""

    def test_override_replaces_default_header(self) -> None:
        msg = _commit.build_commit_message(
            _task(), subject_override="✨ feat(D-054): enriquecer commit"
        )
        self.assertTrue(msg.startswith("✨ feat(D-054): enriquecer commit\n\n"), msg)
        self.assertNotIn("feature(D-054):", msg)

    def test_override_preserves_body_and_task_footer(self) -> None:
        msg = _commit.build_commit_message(
            _task(), subject_override="✨ feat(D-054): x"
        )
        self.assertIn("Validacoes:", msg)
        self.assertIn("Arquivos:", msg)
        self.assertTrue(msg.endswith("\n\nTask: D-054"), msg)

    def test_override_uses_only_first_line(self) -> None:
        msg = _commit.build_commit_message(
            _task(), subject_override="feat(D-054): subject\nlinha extra ignorada"
        )
        self.assertTrue(msg.startswith("feat(D-054): subject\n\n"), msg)
        self.assertNotIn("linha extra ignorada", msg)

    def test_blank_override_falls_back_to_default_header(self) -> None:
        msg = _commit.build_commit_message(_task(), subject_override="   ")
        self.assertTrue(msg.startswith("feature(D-054):"), msg)


class EmptyFieldTests(unittest.TestCase):
    def test_empty_fields_omit_their_blocks_but_keep_header_and_footer(self) -> None:
        msg = _commit.build_commit_message(
            _task(summary=[], validations=[], modifiedFiles=[])
        )
        self.assertEqual(
            msg,
            "feature(D-054): Enriquecer mensagem de commit com resumo do que foi feito"
            "\n\nTask: D-054",
        )

    def test_none_placeholder_is_filtered_from_files(self) -> None:
        msg = _commit.build_commit_message(
            _task(modifiedFiles=[MSG_NONE_PLACEHOLDER, "core/src/_commit.py"])
        )
        self.assertNotIn(MSG_NONE_PLACEHOLDER, msg)
        self.assertIn("- core/src/_commit.py", msg)

    def test_blank_strings_are_ignored(self) -> None:
        msg = _commit.build_commit_message(
            _task(summary=["  ", ""], validations=[" "])
        )
        self.assertNotIn("Validacoes:", msg)
        # Sem summary visivel, o primeiro bloco apos o header e o de arquivos.
        self.assertIn("Arquivos:", msg)


if __name__ == "__main__":
    unittest.main()
