"""Faxina da pasta pai do projeto: worktrees inativas e arquivos soltos (D-202).

Em 2026-10-29 a pasta pai dos projetos (C:/DEV) tinha 31 pastas e 75
arquivos soltos: worktrees de demandas ja integradas que ninguem removeu e
auditorias, logs de portao e mensagens que agentes escreveram fora de
qualquer projeto. A faxina so LISTA; remover e decisao do dono, item por
item (`--remove`), e passa pelos mesmos caminhos seguros do
`worktree remove` (juncoes desfeitas antes, recusa com mudanca local).

Worktree inativa = registrada no git deste projeto, FORA da arvore principal
(as de `.claude/worktrees/` sao do app, de sessoes que podem estar vivas), e
(a) a demanda dela esta Integrada/Finalizada/Cancelada ou (b) sem demanda, a
branch ja esta contida na base. Com mudanca local ela nao e proposta: vai
para `kept` com o porque.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

from _constants import (
    DELIVERY_BASE_BRANCH_DEFAULT,
    PROCESS_FILE,
    ROOT,
    STATUS_CANCELLED,
    STATUS_FINISHED,
    STATUS_INTEGRATED,
    STATUS_VALIDATED,
)
from _git_ops import git_output, git_worktree_remove, run_git
from _state import read_json
from _tasks import list_tasks, save_task
from _worktree import find_links, remove_worktree

# Validada e o status padrao do finish (terminal, como Finalizada).
INACTIVE_STATUSES = frozenset({STATUS_INTEGRATED, STATUS_FINISHED, STATUS_VALIDATED, STATUS_CANCELLED})
# Branch do modelo `{idLower}-{slug}`: `d-911-palco-limpo` -> D-911.
BRANCH_ID_RE = re.compile(r"^([a-z])-(\d+)-")
# Arquivos do sistema que nao sao "soltos" de ninguem.
SYSTEM_FILES = frozenset({"desktop.ini", "thumbs.db", ".ds_store"})


def _norm(path: Path) -> str:
    return os.path.normcase(str(path.resolve()))


def _same(a: Path, b: Path) -> bool:
    return _norm(a) == _norm(b)


def _inside_root(path: Path) -> bool:
    root = _norm(ROOT)
    return _norm(path) == root or _norm(path).startswith(root.rstrip(os.sep) + os.sep)


def _registered_worktrees() -> list[dict[str, Any]]:
    """`git worktree list --porcelain` sem a arvore principal."""
    output = git_output(ROOT, "worktree", "list", "--porcelain") or ""
    entries: list[dict[str, Any]] = []
    for block in output.split("\n\n"):
        entry: dict[str, Any] = {}
        for line in block.splitlines():
            key, _, value = line.partition(" ")
            if key == "worktree":
                entry["path"] = Path(value)
            elif key == "branch":
                entry["branch"] = value.removeprefix("refs/heads/")
            elif key == "prunable":
                entry["prunable"] = True
        if entry.get("path") and not _inside_root(entry["path"]):
            entries.append(entry)
    return entries


def _merged(branch: str, base: str) -> bool:
    for ref in (f"origin/{base}", base):
        if git_output(ROOT, "rev-parse", "--verify", "--quiet", ref) is None:
            continue
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", branch, ref],
            cwd=ROOT, capture_output=True,
        )
        return result.returncode == 0
    return False


def _inactive_reason(entry: dict[str, Any], task: dict[str, Any] | None, base: str) -> str | None:
    if task is not None:
        status = task.get("status")
        return f"demanda {task['id']} {status}" if status in INACTIVE_STATUSES else None
    branch = entry.get("branch")
    if branch and branch != base and _merged(branch, base):
        return f"sem demanda, branch ja contida em {base}"
    return None


def _task_for(entry: dict[str, Any], tasks: list[dict[str, Any]]) -> dict[str, Any] | None:
    for task in tasks:
        worktree = task.get("worktree") or {}
        if worktree.get("path") and _same(ROOT / worktree["path"], entry["path"]):
            return task
    branch = entry.get("branch") or ""
    found = next((t for t in tasks if branch and (t.get("worktree") or {}).get("branch") == branch), None)
    if found is None:
        # Demanda antiga sem o worktree gravado: o id vem do prefixo da branch.
        match = BRANCH_ID_RE.match(branch)
        task_id = f"{match.group(1).upper()}-{match.group(2)}" if match else None
        found = next((t for t in tasks if task_id and t.get("id") == task_id), None)
    return found


def _loose_files() -> list[dict[str, Any]]:
    """Arquivos soltos na pasta pai: ela deveria ter so pastas de projeto."""
    found: list[dict[str, Any]] = []
    try:
        children = sorted(ROOT.parent.iterdir(), key=lambda p: p.name.lower())
    except OSError:
        return found
    for child in children:
        if child.name.lower() in SYSTEM_FILES or child.is_symlink() or not child.is_file():
            continue
        found.append({"path": str(child), "bytes": child.stat().st_size})
    return found


def scan(quick: bool = False) -> dict[str, Any]:
    """O relatorio da faxina. Leitura pura: nada e criado nem removido.

    `quick` (hook SessionStart) pula o `git status` de cada worktree - em
    repo grande ele custa segundos por worktree; a lista completa confere.
    """
    base = (read_json(PROCESS_FILE, {}).get("delivery") or {}).get("baseBranch") or DELIVERY_BASE_BRANCH_DEFAULT
    tasks = list_tasks()
    worktrees: list[dict[str, Any]] = []
    kept: list[dict[str, Any]] = []
    prunable = 0
    for entry in _registered_worktrees():
        if entry.get("prunable") or not entry["path"].exists():
            prunable += 1
            continue
        task = _task_for(entry, tasks)
        why = _inactive_reason(entry, task, base)
        if why is None:
            continue
        item = {"path": str(entry["path"]), "branch": entry.get("branch"),
                "task": task["id"] if task else None, "why": why}
        if quick:
            worktrees.append(item)
            continue
        status = git_output(entry["path"], "status", "--porcelain")
        if status is None:
            kept.append({**item, "why": f"{why}; git status falhou, conferir a mao"})
        elif status:
            kept.append({**item, "why": f"{why}; tem mudanca local nao commitada"})
        else:
            worktrees.append(item)
    return {"parent": str(ROOT.parent), "worktrees": worktrees, "kept": kept,
            "files": _loose_files(), "prunable": prunable}


def _plural(count: int, one: str, many: str) -> str:
    return f"{count} {one if count == 1 else many}"


def session_line(report: dict[str, Any]) -> str:
    """Uma linha para o hook SessionStart; vazia quando nao ha o que limpar."""
    parts = []
    if report["worktrees"]:
        parts.append(_plural(len(report["worktrees"]), "worktree inativa", "worktrees inativas"))
    if report["files"]:
        parts.append(_plural(len(report["files"]), "arquivo solto", "arquivos soltos")
                     + f" em {report['parent']}")
    if not parts:
        return ""
    return (f"Guia Fluxo - faxina: {' e '.join(parts)}. "
            "Rode `guia cleanup` para ver a lista; nada e removido sem o ok do dono.")


def render(report: dict[str, Any]) -> str:
    lines = [f"Faxina de {report['parent']} (so lista: nada e removido sem --remove)."]
    if report["worktrees"]:
        lines.append("Worktrees inativas:")
        lines += [f"  - {w['path']}  [{w['why']}]" for w in report["worktrees"]]
    if report["kept"]:
        lines.append("Inativas mas mantidas (conferir a mao):")
        lines += [f"  - {w['path']}  [{w['why']}]" for w in report["kept"]]
    if report["files"]:
        lines.append(f"Arquivos soltos em {report['parent']}:")
        lines += [f"  - {Path(f['path']).name}  ({f['bytes']} bytes)" for f in report["files"]]
    if report["prunable"]:
        lines.append(f"Registros de worktree sem pasta: {report['prunable']} (`--remove all` roda `git worktree prune`).")
    if len(lines) == 1:
        lines.append("Nada a limpar.")
    else:
        lines.append("Com o ok do dono: `guia cleanup --remove <caminho|D-NNN|arquivo>` (repetivel) ou `--remove all`.")
    return "\n".join(lines)


def _match(target: str, report: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    for item in report["worktrees"]:
        if target.upper() == (item["task"] or "").upper() or _same(Path(target), Path(item["path"])):
            return "worktree", item
    candidate = Path(target) if Path(target).is_absolute() else ROOT.parent / target
    for item in report["files"]:
        if _same(candidate, Path(item["path"])):
            return "file", item
    return None


def _remove_worktree_item(item: dict[str, Any]) -> None:
    path = Path(item["path"])
    task = next((t for t in list_tasks() if t["id"] == item["task"]), None) if item["task"] else None
    recorded = (task or {}).get("worktree") or {}
    if task is not None and recorded.get("path") and _same(ROOT / recorded["path"], path):
        # Pelo caminho seguro do `worktree remove`: desfaz as juncoes gravadas.
        remove_worktree(task)
        save_task(task)
    else:
        leftovers = find_links(path)
        if leftovers:
            raise SystemExit(f"Recusado: {path} tem links que a remocao poderia atravessar: {leftovers}")
        git_worktree_remove(path)
    holder = path.parent
    if holder != ROOT.parent and holder.is_dir() and not any(holder.iterdir()):
        holder.rmdir()


def remove(targets: list[str]) -> list[str]:
    """Remove so o que a faxina propos e o dono escolheu; valida tudo antes."""
    report = scan()
    chosen: list[tuple[str, dict[str, Any]]] = []
    if [t.lower() for t in targets] == ["all"]:
        chosen = [("worktree", w) for w in report["worktrees"]] + [("file", f) for f in report["files"]]
    else:
        refused = []
        for target in targets:
            match = _match(target, report)
            if match is None:
                refused.append(target)
            elif match not in chosen:
                chosen.append(match)
        if refused:
            raise SystemExit(
                "Recusado: a faxina nao propoe " + ", ".join(refused)
                + " (so worktree inativa sem mudanca local ou arquivo solto da pasta pai). Nada foi removido."
            )
    done: list[str] = []
    for kind, item in chosen:
        try:
            if kind == "worktree":
                _remove_worktree_item(item)
            else:
                Path(item["path"]).unlink()
        except (OSError, subprocess.CalledProcessError) as exc:
            raise SystemExit(f"Falhou ao remover {item['path']}: {exc}. Removidos antes: {done}") from None
        done.append(item["path"])
    if [t.lower() for t in targets] == ["all"] and report["prunable"]:
        run_git("worktree", "prune", check=False)
    return done


__all__ = ["remove", "render", "scan", "session_line"]
