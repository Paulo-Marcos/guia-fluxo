"""Worktree da demanda: criacao por modelo, juncoes e remocao segura.

Modo `direct` (historico, achados 2.9/2.13):
    Branch: codex/<slug>
    Path:   .claude/worktrees/<slug>

Modo `pr` (D-113, R1 `delivery.worktree`):
    Path:   ..\\{repo}-{idCompact}      (ex.: ..\\gerador-cortes-d886)
    Branch: {idLower}-{slug}            (ex.: d-886-nota-e-porque)
    From:   origin/{baseBranch}
    envFiles copiados da principal; junctions criadas apontando para ela.

Remocao (D-113, R10): as juncoes declaradas sao desfeitas ANTES do
`git worktree remove`, e qualquer link que sobrar no worktree faz a remocao
recusar - em 05/10 um `worktree remove --force` atravessou uma juncao e
apagou o `node_modules` da arvore principal (D-880 no gerador-cortes).
"""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any

from _clock import today
from _constants import (
    DELIVERY_BASE_BRANCH_DEFAULT,
    DELIVERY_MODE,
    DELIVERY_MODE_PR,
    PROCESS_FILE,
    ROOT,
)
from _git_ops import git_branch_exists, git_output, git_worktree_add, git_worktree_remove, run_git
from _paths import slugify
from _state import read_json

WORKTREE_PATH_TEMPLATE_DEFAULT = "../{repo}-{idCompact}"
WORKTREE_BRANCH_TEMPLATE_DEFAULT = "{idLower}-{slug}"
WORKTREE_FROM_TEMPLATE_DEFAULT = "origin/{baseBranch}"
BRANCH_SLUG_MAX = 50


def worktree_settings() -> dict[str, Any]:
    """`delivery.worktree` com os padroes do modo `pr` (R1)."""
    delivery = read_json(PROCESS_FILE, {}).get("delivery") or {}
    worktree = delivery.get("worktree") or {}
    return {
        "path": worktree.get("path") or WORKTREE_PATH_TEMPLATE_DEFAULT,
        "branch": worktree.get("branch") or WORKTREE_BRANCH_TEMPLATE_DEFAULT,
        "from": worktree.get("from") or WORKTREE_FROM_TEMPLATE_DEFAULT,
        "baseBranch": delivery.get("baseBranch") or DELIVERY_BASE_BRANCH_DEFAULT,
        "envFiles": list(worktree.get("envFiles") or []),
        "junctions": list(worktree.get("junctions") or []),
    }


def _ascii_fold(value: str) -> str:
    """`junções` -> `juncoes`: o slugify troca letra acentuada por hifen."""
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")


def _render(template: str, task: dict[str, Any], base_branch: str) -> str:
    task_id = str(task["id"])
    return template.format(
        repo=ROOT.name,
        id=task_id,
        idLower=task_id.lower(),
        idCompact=task_id.lower().replace("-", ""),
        slug=slugify(_ascii_fold(task.get("title", "")), max_length=BRANCH_SLUG_MAX),
        baseBranch=base_branch,
    )


def _is_link(path: Path) -> bool:
    """Link simbolico ou ponto de reparse (juncao do Windows), sem segui-lo."""
    try:
        info = os.lstat(path)
    except OSError:
        return False
    if stat.S_ISLNK(info.st_mode):
        return True
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(getattr(info, "st_file_attributes", 0) & reparse)


def find_links(root: Path) -> list[Path]:
    """Links dentro de `root`, sem descer neles (nem no `.git`).

    `os.walk` no Windows desce em juncoes ate o Python 3.12; aqui cada pasta
    e checada antes de entrar.
    """
    found: list[Path] = []
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            entries = list(os.scandir(current))
        except OSError:
            continue
        for entry in entries:
            path = Path(entry.path)
            if current == root and entry.name == ".git":
                continue
            if _is_link(path):
                found.append(path)
            elif entry.is_dir(follow_symlinks=False):
                stack.append(path)
    return found


def _make_junction(link: Path, target: Path) -> None:
    if os.name == "nt":
        # Sem `cmd /c mklink`: o cmd reinterpreta a linha e `&` no nome (que
        # vem do process.json versionado) viraria outro comando. A API e a
        # mesma que os testes do CPython usam para criar juncoes.
        import _winapi

        _winapi.CreateJunction(str(target), str(link))
    else:
        os.symlink(target, link, target_is_directory=True)


def _remove_link(link: Path) -> None:
    """Remove so o link (nunca o conteudo do destino)."""
    if not _is_link(link):
        raise SystemExit(f"Recusado: {link} deveria ser uma juncao e e uma pasta comum.")
    if os.name == "nt":
        os.rmdir(link)
    else:
        os.unlink(link)


def _inside(rel: str) -> str:
    """`envFiles`/`junctions` sao relativos e ficam dentro do worktree.

    Vem do process.json versionado: um `../fora` faria o motor copiar arquivo
    ou criar link fora do worktree (e da principal).
    """
    candidate = Path(rel)
    if candidate.is_absolute() or ".." in candidate.parts or not candidate.parts:
        raise SystemExit(f"delivery.worktree: caminho invalido {rel!r} - use relativo, sem '..'.")
    return rel


def _prepare(worktree_path: Path, settings: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Copia os envFiles e cria as juncoes declaradas; devolve o que fez."""
    for rel in [*settings["envFiles"], *settings["junctions"]]:
        _inside(rel)
    copied: list[str] = []
    for rel in settings["envFiles"]:
        source, dest = ROOT / rel, worktree_path / rel
        if source.is_file() and not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            copied.append(rel)
        elif not source.is_file():
            print(f"Guia Fluxo: envFile ausente na principal, nao copiado: {rel}", file=sys.stderr)
    linked: list[str] = []
    for rel in settings["junctions"]:
        target, link = ROOT / rel, worktree_path / rel
        if not target.is_dir():
            print(f"Guia Fluxo: juncao sem destino na principal, nao criada: {rel}", file=sys.stderr)
            continue
        if link.exists() or _is_link(link):
            print(f"Guia Fluxo: {rel} ja existe no worktree, juncao nao criada.", file=sys.stderr)
            continue
        link.parent.mkdir(parents=True, exist_ok=True)
        _make_junction(link, target)
        linked.append(rel)
    return copied, linked


def create_worktree(
    task: dict[str, Any],
    path: str | None = None,
    branch: str | None = None,
    remove_on_finish: bool = True,
) -> dict[str, Any]:
    """Cria o worktree da demanda pelo modelo do modo `pr` (D-113)."""
    settings = worktree_settings()
    path = path or _render(settings["path"], task, settings["baseBranch"])
    start = _render(settings["from"], task, settings["baseBranch"])
    # D-130: demanda com PR (ex.: aberto pela nuvem) segue a branch do PR, a
    # partir do que ja foi empurrado, em vez de nascer de novo da base.
    pr_branch = (task.get("pr") or {}).get("branch")
    if not branch and pr_branch:
        run_git("fetch", "-q", "origin", pr_branch, check=False)
        if git_output(ROOT, "rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{pr_branch}"):
            branch, start = pr_branch, f"origin/{pr_branch}"
    branch = branch or _render(settings["branch"], task, settings["baseBranch"])
    if git_branch_exists(branch):
        raise SystemExit(f"Branch ja existe: {branch}. Use --branch <outro-nome> ou apague a anterior.")
    absolute_path = (ROOT / path).resolve()
    if absolute_path.exists():
        raise SystemExit(f"Pasta ja existe: {absolute_path}. Remova-a ou use --path.")
    for rel in [*settings["envFiles"], *settings["junctions"]]:
        _inside(rel)
    if start.startswith("origin/"):
        run_git("fetch", "-q", "origin", start.split("/", 1)[1], check=False)
    git_worktree_add(branch, absolute_path, start)
    copied, linked = _prepare(absolute_path, settings)
    task["worktree"] = {
        "enabled": True,
        "path": path,
        "branch": branch,
        "from": start,
        "created": True,
        "removeOnFinish": remove_on_finish,
        "envFiles": copied,
        "junctions": linked,
    }
    return task["worktree"]


def remove_worktree(task: dict[str, Any], force: bool = False) -> None:
    """Desfaz as juncoes, confere que nao sobrou link e remove o worktree."""
    worktree = task.get("worktree") or {}
    path = worktree.get("path")
    if not path:
        raise SystemExit(f"{task['id']} nao tem worktree registrado.")
    absolute_path = (ROOT / path).resolve()
    if absolute_path == ROOT.resolve():
        raise SystemExit("Recusado: o worktree registrado e a propria arvore principal.")
    if absolute_path.exists():
        for rel in worktree.get("junctions") or []:
            link = absolute_path / _inside(rel)
            if _is_link(link):
                _remove_link(link)
        leftovers = find_links(absolute_path)
        if leftovers:
            listed = "\n".join(f"  - {p}" for p in leftovers)
            raise SystemExit(
                "Recusado: o worktree ainda tem links (juncoes/simbolicos) que a remocao "
                "poderia atravessar, apagando o destino (D-880):\n"
                f"{listed}\n"
                "Desfaca cada um (Windows: `cmd /c rmdir <link>`, que apaga so o link) e repita."
            )
        try:
            git_worktree_remove(absolute_path, force=force)
        except subprocess.CalledProcessError:
            raise SystemExit(
                f"O git recusou remover {absolute_path} (mudancas nao commitadas?). "
                "Confira o que ha la; para descartar, repita com --force."
            ) from None
    worktree["removedAt"] = today()
    worktree["created"] = False
    worktree["junctions"] = []


def attach_worktree(
    task: dict[str, Any],
    args: argparse.Namespace,
    item: dict[str, Any],
) -> None:
    if DELIVERY_MODE == DELIVERY_MODE_PR:
        if args.create_worktree:
            create_worktree(task, args.worktree_path, args.branch, args.remove_worktree_on_finish)
        else:
            settings = worktree_settings()
            task["worktree"] = {
                "enabled": True,
                "path": args.worktree_path or _render(settings["path"], task, settings["baseBranch"]),
                "branch": args.branch or _render(settings["branch"], task, settings["baseBranch"]),
                "created": False,
                "removeOnFinish": args.remove_worktree_on_finish,
            }
        return
    slug = slugify(f"{task['id']}-{item['title']}")
    path = args.worktree_path or f".claude/worktrees/{slug}"
    branch = args.branch or f"codex/{slug}"
    task["worktree"] = {
        "enabled": True,
        "path": path,
        "branch": branch,
        "created": False,
        "removeOnFinish": args.remove_worktree_on_finish,
    }
    if not args.create_worktree:
        return
    if git_branch_exists(branch):
        raise SystemExit(
            f"Branch ja existe: {branch}. Use --branch <outro-nome> ou apague o anterior."
        )
    absolute_path = ROOT / path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    git_worktree_add(branch, absolute_path)
    task["worktree"]["created"] = True


def cleanup_task_worktree(task: dict[str, Any], commit_requested: bool) -> None:
    worktree = task.get("worktree") or {}
    if not worktree.get("enabled") or not worktree.get("removeOnFinish"):
        return
    if DELIVERY_MODE == DELIVERY_MODE_PR:
        # D-113: no modo `pr` o finish nunca commita (D-111) e o fechamento
        # vem depois do merge - e a hora de remover. Sem --force: worktree com
        # trabalho nao commitado fica, com aviso, em vez de sumir calado.
        if not worktree.get("created"):
            return
        try:
            remove_worktree(task)
        except (SystemExit, subprocess.CalledProcessError) as exc:
            print(f"Guia Fluxo: worktree mantido ({worktree.get('path')}): {exc}", file=sys.stderr)
        return
    # --no-commit means "dry close": leave the worktree alone (achado 2.9)
    if not commit_requested:
        return
    path = worktree.get("path")
    if not path:
        return
    absolute_path = (ROOT / path).resolve()
    if absolute_path == ROOT.resolve():
        print("WORKTREE_CLEANUP_SKIPPED=current-root")
        return
    if not absolute_path.exists():
        worktree["removedAt"] = today()
        worktree["created"] = False
        return
    git_worktree_remove(absolute_path, force=True)
    worktree["removedAt"] = today()
    worktree["created"] = False


__all__ = [
    "attach_worktree",
    "cleanup_task_worktree",
    "create_worktree",
    "find_links",
    "remove_worktree",
    "worktree_settings",
]
