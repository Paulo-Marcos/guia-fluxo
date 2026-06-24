"""Build the commit for a finished task.

Centralizes the normalization step (Windows backslash -> forward slash)
that previously caused `commit_task` to see staged files as unrelated
(achado 2.4).
"""

from __future__ import annotations

import subprocess
from typing import Any

from _constants import (
    MSG_GIT_NOT_FOUND,
    MSG_NO_FILES_FOR_COMMIT,
    MSG_NONE_PLACEHOLDER,
    MSG_UNRELATED_STAGED,
)
from _git_ops import git_commit, git_staged_files, has_git
from _paths import normalize_path


def build_commit_message(
    task: dict[str, Any],
    commit_body: str | None = None,
    subject_override: str | None = None,
) -> str:
    """Monta a mensagem de commit enriquecida (D-054, absorve B-019).

    Formato Conventional Commits, preservando a convencao do repo (`feature:`/
    `bug:`/`chore:`, nao `feat`/`fix`) e adicionando o id da task como *scope*:

        {kind}({id}): {title}

        <summary - o que foi feito>

        Validacoes:
        - <validacao que passou>

        Arquivos:
        - <arquivo modificado>

        <texto livre de --commit-body, se houver>

        Task: {id}

    `subject_override` (D-054 ajuste): quando o projeto/usuario tem uma skill de
    convencao de commits propria, o agente gera o subject por ela e passa aqui;
    ele SUBSTITUI a linha de header padrao (ex.: `feat(D-054): ...` com gitmoji),
    mas o corpo estruturado e o rodape `Task: {id}` permanecem - assim a
    convencao do usuario e honrada sem quebrar a ancora estavel dos parsers. So a
    primeira linha do override e usada como subject (Conventional Commits = 1
    linha de assunto).

    O rodape `Task: {id}` e mantido literal e por ultimo: e a ancora estavel que
    ferramentas/parsers existentes consomem. Cada bloco do corpo so aparece se
    tiver conteudo, mantendo a mensagem previsivel quando os campos estao vazios.
    """
    if subject_override and subject_override.strip():
        header = subject_override.strip().splitlines()[0].strip()
    else:
        header = f"{task['kind']}({task['id']}): {task['title']}"
    blocks: list[str] = []

    summary = [str(line).strip() for line in task.get("summary", []) if str(line).strip()]
    if summary:
        blocks.append("\n".join(f"- {line}" for line in summary))

    validations = [str(v).strip() for v in task.get("validations", []) if str(v).strip()]
    if validations:
        blocks.append("\n".join(["Validacoes:", *(f"- {v}" for v in validations)]))

    files = [
        value
        for value in task.get("modifiedFiles", [])
        if value and value != MSG_NONE_PLACEHOLDER
    ]
    if files:
        blocks.append("\n".join(["Arquivos:", *(f"- {value}" for value in files)]))

    if commit_body and commit_body.strip():
        blocks.append(commit_body.strip())

    blocks.append(f"Task: {task['id']}")
    return header + "\n\n" + "\n\n".join(blocks)


def commit_task(
    task: dict[str, Any],
    commit_body: str | None = None,
    subject_override: str | None = None,
) -> None:
    files = [value for value in task.get("modifiedFiles", []) if value != MSG_NONE_PLACEHOLDER]
    if not files:
        raise SystemExit(MSG_NO_FILES_FOR_COMMIT)
    if not has_git():
        raise SystemExit(MSG_GIT_NOT_FOUND)
    expected = {normalize_path(value) for value in files}
    staged = {normalize_path(value) for value in git_staged_files()}
    unexpected = sorted(staged - expected)
    if unexpected:
        names = ", ".join(unexpected)
        raise SystemExit(MSG_UNRELATED_STAGED.format(names=names))
    message = build_commit_message(task, commit_body, subject_override)
    try:
        git_commit(files, message)
    except FileNotFoundError:
        raise SystemExit(MSG_GIT_NOT_FOUND)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode)


__all__ = ["build_commit_message", "commit_task"]
