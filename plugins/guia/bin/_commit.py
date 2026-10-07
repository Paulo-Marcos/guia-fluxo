"""Build the commit for a finished task.

Centralizes the normalization step (Windows backslash -> forward slash)
that previously caused `commit_task` to see staged files as unrelated
(achado 2.4).
"""

from __future__ import annotations

import subprocess
from typing import Any

import _locks
from _constants import (
    COMMIT_FORMAT_GITMOJI,
    COMMIT_FORMAT_LEGACY,
    COMMIT_GITMOJI_BY_KIND,
    DELIVERY_BASE_BRANCH_DEFAULT,
    MSG_GIT_NOT_FOUND,
    MSG_NO_FILES_FOR_COMMIT,
    MSG_NONE_PLACEHOLDER,
    PROCESS_FILE,
)
from _git_ops import git_commit, git_ignored_files, has_git, name_status_against_base
from _state import read_json


def commit_settings() -> dict[str, Any]:
    """`delivery.commit` + `delivery.baseBranch` do process.json, com padroes.

    Sem `delivery`, o formato e o legado: nada muda para quem nao configurou.
    """
    delivery = read_json(PROCESS_FILE, {}).get("delivery") or {}
    commit = delivery.get("commit") or {}
    fmt = commit.get("format", COMMIT_FORMAT_LEGACY)
    return {
        "format": fmt if fmt in (COMMIT_FORMAT_LEGACY, COMMIT_FORMAT_GITMOJI) else COMMIT_FORMAT_LEGACY,
        "coAuthor": commit.get("coAuthor") or None,
        "baseBranch": delivery.get("baseBranch") or DELIVERY_BASE_BRANCH_DEFAULT,
    }


def _product_files(task: dict[str, Any]) -> list[str]:
    return [value for value in task.get("modifiedFiles", []) if value and value != MSG_NONE_PLACEHOLDER]


def unlock_trailers(files: list[str], reasons: list[str], base_branch: str) -> list[str]:
    """Marcas `[unlock:<trava>] motivo: <motivo>` para as travas que `files` tocam.

    D-112 (R10): a operacao de cada arquivo (adicao, modificacao, delecao) vem
    do git contra a base, nao do disco - arquivo novo ja existe no disco e
    passaria por modificacao, escapando da trava de adicoes. `reasons` aceita
    `<trava>=<motivo>` (por trava) ou `<motivo>` (vale para as demais). O
    motivo e obrigatorio: trava tocada sem motivo recusa, citando cada uma.
    """
    lines = name_status_against_base(files, base_branch)
    blocked = _locks.lock_api.find_blocked(_locks.lock_api.events_from_name_status(lines))
    lock_ids: list[str] = []
    for match in blocked:
        if match.lock["id"] not in lock_ids:
            lock_ids.append(match.lock["id"])
    if not lock_ids:
        return []
    per_lock: dict[str, str] = {}
    default: str | None = None
    for reason in reasons:
        key, sep, value = reason.partition("=")
        if sep and key.strip() in lock_ids and value.strip():
            per_lock[key.strip()] = value.strip()
        elif reason.strip():
            default = reason.strip()
    missing = [lock_id for lock_id in lock_ids if lock_id not in per_lock and not default]
    if missing:
        detail = "\n".join(
            f"  - {lock_id}: {', '.join(sorted({m.path for m in blocked if m.lock['id'] == lock_id}))}"
            for lock_id in missing
        )
        raise SystemExit(
            "Os arquivos da demanda tocam travas sem motivo declarado:\n"
            f"{detail}\n"
            'Passe --unlock-reason "<trava>=<motivo>" (ou um --unlock-reason "<motivo>" '
            "para todas). A autorizacao do dono vem antes: o motivo registra por que ela foi dada."
        )
    return [f"[unlock:{lock_id}] motivo: {per_lock.get(lock_id, default)}" for lock_id in lock_ids]


def compose_commit_message(
    task: dict[str, Any],
    unlock_reasons: list[str] | None = None,
    commit_body: str | None = None,
    subject_override: str | None = None,
) -> str:
    """Mensagem final no formato configurado (consumida por finish e commit-message)."""
    settings = commit_settings()
    if settings["format"] != COMMIT_FORMAT_GITMOJI:
        return build_commit_message(task, commit_body, subject_override)
    trailers = unlock_trailers(_product_files(task), unlock_reasons or [], settings["baseBranch"])
    return build_commit_message(
        task,
        commit_body,
        subject_override,
        fmt=COMMIT_FORMAT_GITMOJI,
        trailers=trailers,
        co_author=settings["coAuthor"],
    )


def build_commit_message(
    task: dict[str, Any],
    commit_body: str | None = None,
    subject_override: str | None = None,
    *,
    fmt: str = COMMIT_FORMAT_LEGACY,
    trailers: list[str] | None = None,
    co_author: str | None = None,
) -> str:
    """Monta a mensagem de commit enriquecida (D-054, absorve B-019).

    D-112: com `fmt="gitmoji-conventional"` o header vira
    `<emoji> <tipo>(ID): titulo` e a mensagem fecha com `trailers` (as marcas
    [unlock:]) e o `Co-Authored-By`; o corpo e so o `commit_body` (o porque),
    sem summary nem os blocos Validacoes/Arquivos/Task - o formato do processo
    por PR. O legado abaixo segue identico.

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
    if fmt == COMMIT_FORMAT_GITMOJI:
        return _build_gitmoji_message(task, commit_body, subject_override, trailers or [], co_author)
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


def _build_gitmoji_message(
    task: dict[str, Any],
    commit_body: str | None,
    subject_override: str | None,
    trailers: list[str],
    co_author: str | None,
) -> str:
    if subject_override and subject_override.strip():
        header = subject_override.strip().splitlines()[0].strip()
    else:
        prefix = COMMIT_GITMOJI_BY_KIND.get(task.get("kind", ""), COMMIT_GITMOJI_BY_KIND["chore"])
        header = f"{prefix}({task['id']}): {task['title']}"
    # O corpo e o porque, escrito pelo agente (--body/--commit-body). O
    # `summary` da demanda nao entra: e registro de bastidor ("Em
    # desenvolvimento desde...", "Demanda criada via..."), nao motivo.
    blocks: list[str] = []
    if commit_body and commit_body.strip():
        blocks.append(commit_body.strip())
    if trailers:
        blocks.append("\n".join(trailers))
    if co_author:
        blocks.append(f"Co-Authored-By: {co_author}")
    return header + ("\n\n" + "\n\n".join(blocks) if blocks else "")


def commit_task(
    task: dict[str, Any],
    commit_body: str | None = None,
    subject_override: str | None = None,
    unlock_reasons: list[str] | None = None,
) -> None:
    files = [value for value in task.get("modifiedFiles", []) if value != MSG_NONE_PLACEHOLDER]
    if not has_git():
        raise SystemExit(MSG_GIT_NOT_FOUND)
    # D-111 (D-579): toda demanda nasce com `.guia/DEMANDAS.md` em
    # modifiedFiles; com o estado no .gitignore, `git add` abortava o commit
    # inteiro. Arquivo ignorado nao e versionado aqui: sai do pathspec.
    ignored = git_ignored_files(files)
    files = [value for value in files if value not in ignored]
    if not files:
        raise SystemExit(MSG_NO_FILES_FOR_COMMIT)
    # D-105: NAO abortamos mais quando ha arquivos alheios staged. Antes, um
    # `git add` de outra demanda paralela fazia o finish recusar (staged -
    # expected). Agora `git_commit` commita por pathspec (`commit -- <files>`),
    # entao arquivos alheios no index simplesmente nao entram neste commit -
    # ficam intactos para a demanda dona fechar. Nada a checar aqui.
    message = compose_commit_message(task, unlock_reasons, commit_body, subject_override)
    try:
        git_commit(files, message)
    except FileNotFoundError:
        raise SystemExit(MSG_GIT_NOT_FOUND)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode)


__all__ = [
    "build_commit_message",
    "commit_settings",
    "commit_task",
    "compose_commit_message",
    "unlock_trailers",
]
