"""Faxina da pasta pai do projeto: worktrees inativas e arquivos soltos (D-202).

Em 2026-10-29 a pasta pai dos projetos (C:/DEV) tinha 31 pastas e 75
arquivos soltos: worktrees de demandas ja integradas que ninguem removeu e
auditorias, logs de portao e mensagens que agentes escreveram fora de
qualquer projeto. A faxina so LISTA; remover e decisao do dono, item por
item (`--remove`), e passa pelos mesmos caminhos seguros do
`worktree remove` (juncoes desfeitas antes, recusa com mudanca local).

Worktree inativa = registrada no git deste projeto, FORA da arvore principal
(as de `.claude/worktrees/` sao do app, de sessoes que podem estar vivas), e
com a demanda dela encerrada (Integrada/Finalizada/Validada/Cancelada).
Worktree sem demanda nao e proposta: branch recem-criada tambem "esta contida
na base". Com mudanca local - inclusive arquivo ignorado, como um `.env`, que
o `git worktree remove` apagaria junto - ou HEAD destacado, vai para `kept`.

Arquivo solto = artefato de agente na pasta pai (log, .msg, patch, saida de
comando), nunca dotfile nem documento: um projeto dentro da pasta do usuario
tem `.gitconfig` e `Contrato.docx` ao lado (auditoria do PR #96).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from _artifacts import ARTIFACTS_ROOT, artifacts_root
from _constants import (
    ROOT,
    STATUS_CANCELLED,
    STATUS_FINISHED,
    STATUS_INTEGRATED,
    STATUS_VALIDATED,
)
from _git_ops import git_output, git_worktree_remove, run_git
from _state import read_json
from _tasks import list_tasks, save_task
from _worktree import _is_link, find_links, remove_worktree

# Validada e o status padrao do finish (terminal, como Finalizada).
INACTIVE_STATUSES = frozenset({STATUS_INTEGRATED, STATUS_FINISHED, STATUS_VALIDATED, STATUS_CANCELLED})
# Branch do modelo `{idLower}-{slug}`: `d-911-palco-limpo` -> D-911.
BRANCH_ID_RE = re.compile(r"^([a-z])-(\d+)-")
# Artefato de agente: extensao que so sai de comando (log, mensagem, patch)...
ARTIFACT_SUFFIXES = frozenset({".log", ".msg", ".patch", ".diff", ".rc", ".err", ".out"})
# ...ou texto/relatorio com nome de rascunho de agente. Padroes estritos: um
# documento real (`IRPF2025.txt`, `tsconfig.json`, `cv.md`) nunca casa
# (reauditoria do PR #96), porque a remocao e definitiva.
DRAFT_SUFFIXES = frozenset({".txt", ".md", ".json"})
DRAFT_NAME_RE = re.compile(
    r"^(?:"
    r"(?:.+[-_])?d-?\d{2,4}(?:[-_].*)?"            # id de demanda: d975-files, auditoria-d976-r2
    r"|(?:v|c|t|l|p|ci|msg|ship|audit)\d{1,4}[a-z]?"  # rascunho curto: v12, c968b, msg968, ship957
    r"|vm\d*"
    r"|(?:gate|npmaud|audit|auditoria|ship|commit-msg)[-_].+"  # etapa com separador: gate-x, npmaud-fe
    r")$"
)
# Redirecionamento para `null`/`nul` no shell errado vira arquivo.
NULL_NAMES = frozenset({"null", "nul"})
# Fiapos das worktrees: nao contam como mudanca local.
BENIGN_IGNORED = ("__pycache__/", ".pytest_cache/", ".mypy_cache/", ".ruff_cache/")
SNAPSHOT_FILE = "cleanup-shown.json"


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


def _inactive_reason(task: dict[str, Any] | None) -> str | None:
    if task is None or task.get("status") not in INACTIVE_STATUSES:
        return None
    return f"demanda {task['id']} {task['status']}"


def _local_work(path: Path, task: dict[str, Any]) -> str | None:
    """Por que a remocao perderia algo, ou None se nao perderia nada."""
    status = git_output(path, "status", "--porcelain", "--ignored")
    if status is None:
        return "git status falhou, conferir a mao"
    junctions = {j.strip("/") for j in (task.get("worktree") or {}).get("junctions") or []}
    for line in status.splitlines():
        code, name = line[:2], line[3:].strip('"')
        if code != "!!":
            return "tem mudanca local nao commitada"
        bare = name.rstrip("/")
        benign = any(name == b or name.endswith("/" + b) for b in BENIGN_IGNORED)
        # Juncao gravada so e "nada a perder" se ainda for link: uma pasta
        # real no lugar dela seria apagada pelo `git worktree remove`.
        linked = bare in junctions and _is_link(path / bare)
        if not (benign or linked):
            return f"tem arquivo ignorado que a remocao apagaria ({name})"
    return None


def _is_artifact(path: Path) -> bool:
    name, stem, suffix = path.name.lower(), path.stem.lower(), path.suffix.lower()
    if name.startswith("."):
        return False
    if name in NULL_NAMES or suffix in ARTIFACT_SUFFIXES:
        return True
    if suffix not in DRAFT_SUFFIXES:
        return False
    return bool(DRAFT_NAME_RE.match(stem))


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
    """Artefatos de agente soltos na pasta pai (so arquivo comum, sem link)."""
    found: list[dict[str, Any]] = []
    try:
        children = sorted(ROOT.parent.iterdir(), key=lambda p: p.name.lower())
    except OSError:
        return found
    files = [c for c in children if not c.is_symlink() and c.is_file()]
    # `g-build.txt` ao lado de `g-build.rc`: saida e codigo do mesmo comando.
    command_stems = {c.stem.lower() for c in files if c.suffix.lower() in ARTIFACT_SUFFIXES}
    for child in files:
        draft_twin = child.suffix.lower() in DRAFT_SUFFIXES and child.stem.lower() in command_stems
        if not (_is_artifact(child) or (draft_twin and not child.name.startswith("."))):
            continue
        found.append({"path": str(child), "bytes": child.stat().st_size})
    return found


def scan(quick: bool = False) -> dict[str, Any]:
    """O relatorio da faxina. Leitura pura: nada e criado nem removido.

    `quick` (hook SessionStart) pula o `git status` de cada worktree - em
    repo grande ele custa segundos por worktree; a lista completa confere.
    """
    tasks = list_tasks()
    worktrees: list[dict[str, Any]] = []
    kept: list[dict[str, Any]] = []
    prunable = 0
    for entry in _registered_worktrees():
        if entry.get("prunable") or not entry["path"].exists():
            prunable += 1
            continue
        task = _task_for(entry, tasks)
        why = _inactive_reason(task)
        if why is None or task is None:
            continue
        item = {"path": str(entry["path"]), "branch": entry.get("branch"), "task": task["id"], "why": why}
        if not entry.get("branch"):
            # HEAD destacado: commit fora de branch se perderia com a pasta.
            kept.append({**item, "why": f"{why}; HEAD destacado, conferir a mao"})
            continue
        if quick:
            worktrees.append(item)
            continue
        loss = _local_work(entry["path"], task)
        if loss:
            kept.append({**item, "why": f"{why}; {loss}"})
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


def save_shown(report: dict[str, Any]) -> None:
    """Grava o que o dono viu: `--remove all` vale so para isso."""
    shown = [w["path"] for w in report["worktrees"]] + [f["path"] for f in report["files"]]
    (artifacts_root() / SNAPSHOT_FILE).write_text(json.dumps(shown, ensure_ascii=False), encoding="utf-8")


def _load_shown() -> list[str]:
    path = ARTIFACTS_ROOT / SNAPSHOT_FILE
    return list(read_json(path, [])) if path.is_file() else []


def _match(target: str, report: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    if not target.strip():
        return None
    for item in report["worktrees"]:
        if target.upper() == item["task"].upper() or _same(Path(target), Path(item["path"])):
            return "worktree", item
    candidate = Path(target) if Path(target).is_absolute() else ROOT.parent / target
    for item in report["files"]:
        if _same(candidate, Path(item["path"])):
            return "file", item
    return None


def _remove_worktree_item(item: dict[str, Any]) -> None:
    path = Path(item["path"])
    task = next((t for t in list_tasks() if t["id"] == item["task"]), None)
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
        # So o que a ultima listagem mostrou e ainda vale: arquivo novo desde
        # entao nao entra calado (auditoria do PR #96).
        shown = [_norm(Path(p)) for p in _load_shown()]
        if not shown:
            raise SystemExit("Recusado: rode `guia cleanup` para o dono ver a lista antes de `--remove all`.")
        chosen = [("worktree", w) for w in report["worktrees"] if _norm(Path(w["path"])) in shown]
        chosen += [("file", f) for f in report["files"] if _norm(Path(f["path"])) in shown]
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
        except (OSError, subprocess.CalledProcessError, SystemExit) as exc:
            raise SystemExit(f"Falhou ao remover {item['path']}: {exc}. Removidos antes: {done}") from None
        done.append(item["path"])
    if [t.lower() for t in targets] == ["all"] and report["prunable"]:
        run_git("worktree", "prune", check=False)
    return done


__all__ = ["remove", "render", "save_shown", "scan", "session_line"]
