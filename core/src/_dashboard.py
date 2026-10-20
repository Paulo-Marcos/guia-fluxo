"""Painel local (D-175): os projetos da maquina e as demandas de cada um.

Somente leitura. Diferente do resto do motor, nada aqui usa o `ROOT` global:
o painel olha VARIOS projetos de uma vez, entao cada funcao recebe a raiz do
projeto e le o `.guia/` dela (tasks, fila, process). Quem grava continua
sendo o motor rodado dentro de cada projeto.

O cadastro de projetos mora fora de qualquer projeto, em
`~/.guia/projects.json` (ou `$GUIA_HOME/projects.json`): uma lista de
caminhos que o `dashboard` registra ao rodar num projeto, por `--add` ou por
`--scan` de uma pasta.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from _autonomy import effective_level
from _constants import KIND_MARKER_FALLBACK, KIND_MARKERS, STATUS_TAGS
from _merge_queue import OPEN_STATES, ordered
from _task_view import detail

# Colunas do quadro, na ordem do fluxo. O que nao cai aqui (Validada,
# Finalizada, Cancelada, Resolvida) vai para "concluidas recentes".
STAGES: tuple[tuple[str, str], ...] = (
    ("Backlog", "Backlog"),
    ("Planejada", "Planejada"),
    ("Em desenvolvimento", "Em desenvolvimento"),
    ("Aguardando validacao", "Aguardando validação"),
    ("Em PR", "Em PR"),
    ("Na fila", "Na fila"),
    ("Integrada", "Integrada"),
    ("Bloqueada", "Bloqueada"),
)
_STATUS_ALIASES = {"Aguardando validação": "Aguardando validacao"}
DONE_STATUSES = frozenset({"Validada", "Finalizada", "Cancelada", "Resolvida"})
RECENT_DONE_LIMIT = 8
QUEUE_HISTORY_LIMIT = 6
# Mesmo padrao do executor (_executor.LEASE_STALE_MINUTES_DEFAULT); nao importado
# de la porque o _executor puxa git/gh/worktree, peso que o painel nao precisa.
LEASE_STALE_MINUTES = 10
ENGINE = Path(__file__).resolve().parent / "guia.py"
# Motor que mora dentro do projeto (repo-mae, dogfood, copia manual). Sem
# nenhum (o caso do plugin), vale o do painel. Fica aqui, e nao em
# _dashboard_actions, para o retrato mostrar o motor sem import circular.
PROJECT_ENGINES = (Path("core/src/guia.py"), Path("plugins/guia/bin/guia.py"), Path(".guia-fluxo/bin/guia.py"))
_SCAN_SKIP = frozenset({"node_modules", ".git", ".venv", "venv", "__pycache__", "dist", "build", "bin", "obj"})


# --- cadastro de projetos -----------------------------------------------------


def registry_file() -> Path:
    home = os.environ.get("GUIA_HOME")
    base = Path(home) if home else Path.home() / ".guia"
    return base / "projects.json"


def is_project(path: Path) -> bool:
    """Projeto com estado do Guia: o `tasks.json` mora so na arvore principal,
    entao worktrees de demanda (que tem so o `process.json`) ficam de fora."""
    return (path / ".guia" / "tasks.json").is_file()


def load_projects() -> list[str]:
    try:
        data = json.loads(registry_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    paths = data.get("projects") if isinstance(data, dict) else None
    return [p for p in paths or [] if isinstance(p, str)]


def _save_projects(paths: list[str]) -> None:
    target = registry_file()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"schemaVersion": 1, "projects": paths}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _key(path: str) -> str:
    return os.path.normcase(str(Path(path).resolve()))


def add_projects(paths: list[Path]) -> list[str]:
    """Cadastra os que sao projeto e ainda nao estao; devolve os novos."""
    current = load_projects()
    known = {_key(p) for p in current}
    added: list[str] = []
    for path in paths:
        resolved = str(path.resolve())
        if is_project(path) and _key(resolved) not in known:
            known.add(_key(resolved))
            current.append(resolved)
            added.append(resolved)
    if added:
        _save_projects(current)
    return added


def remove_project(path: Path) -> bool:
    current = load_projects()
    kept = [p for p in current if _key(p) != _key(str(path))]
    if len(kept) == len(current):
        return False
    _save_projects(kept)
    return True


def scan(base: Path, depth: int = 3) -> list[Path]:
    """Pastas sob `base` (ate `depth` niveis) que sao projeto do Guia."""
    found: list[Path] = []

    def walk(folder: Path, level: int) -> None:
        if is_project(folder):
            found.append(folder)
            return  # projeto dentro de projeto nao e o caso comum; para aqui
        if level >= depth:
            return
        try:
            children = sorted(p for p in folder.iterdir() if p.is_dir())
        except OSError:
            return
        for child in children:
            if child.name.startswith(".") or child.name in _SCAN_SKIP:
                continue
            walk(child, level + 1)

    walk(base.resolve(), 0)
    return found


# --- retrato de um projeto ----------------------------------------------------


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _card(task: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    status = _STATUS_ALIASES.get(task.get("status", ""), task.get("status", ""))
    pr = task.get("pr") or {}
    audit = task.get("audit") or {}
    blocks = task.get("blocks") or []
    open_block = next((b for b in reversed(blocks) if isinstance(b, dict) and not b.get("unblockedAt")), None)
    return {
        "id": task.get("id"),
        "kind": task.get("kind"),
        "marker": KIND_MARKERS.get(task.get("kind", ""), KIND_MARKER_FALLBACK),
        "title": task.get("title", ""),
        "status": status,
        "tag": STATUS_TAGS.get(status, ""),
        "updatedAt": task.get("updatedAt"),
        "readyAt": task.get("readyAt"),
        "finishedAt": task.get("finishedAt"),
        "parentId": task.get("parentId"),
        "chat": (task.get("chat") or {}).get("title"),
        "branch": (task.get("worktree") or {}).get("branch"),
        "pr": {"number": pr.get("number"), "url": pr.get("url")} if pr.get("number") else None,
        "audit": audit.get("result"),
        "autonomy": effective_level(task, config),
        "blockedReason": open_block.get("reason") if open_block else None,
        "pending": [p for p in task.get("pending") or [] if isinstance(p, str)],
        # D-192: o que abre ao clicar no cartao (contexto, plano, etapas...).
        "detail": detail(task),
    }


def _executor(root: Path, config: dict[str, Any], now: float) -> dict[str, Any] | None:
    """O executor da fila (D-127) pelo lease: vivo enquanto o batimento e
    mais novo que `queue.leaseStaleMinutes`; None quando nao ha lease."""
    lease = _read(root / ".guia" / "queue" / "executor.lease", None)
    if not isinstance(lease, dict):
        return None
    delivery = config.get("delivery") if isinstance(config.get("delivery"), dict) else {}
    queue_cfg = delivery.get("queue") if isinstance(delivery.get("queue"), dict) else {}
    stale = float(queue_cfg.get("leaseStaleMinutes") or LEASE_STALE_MINUTES) * 60
    try:
        age = max(0.0, now - float(lease.get("heartbeat") or 0))
    except (TypeError, ValueError):
        age = float("inf")
    return {
        "alive": age < stale,
        "pid": lease.get("pid"),
        "host": lease.get("host"),
        "startedAt": lease.get("startedAt"),
        "heartbeatAgeSeconds": None if age == float("inf") else round(age),
    }


def queue_stopped(queue: dict[str, Any]) -> bool:
    """Fila parada: pausada pelo dono ou congelada pela main vermelha. Uma
    regra so para o botao (Retomar em vez de Iniciar executor) e as acoes."""
    return bool(queue.get("paused") or queue.get("frozenReason"))


def _queue(root: Path, by_id: dict[str, dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    data = _read(root / ".guia" / "queue.json", {})
    items = [i for i in data.get("items") or [] if isinstance(i, dict)]

    def status_of(task_id: str) -> str | None:
        task = by_id.get(task_id)
        return task.get("status") if task else None

    line = []
    for position, (item, reason) in enumerate(ordered(items, status_of), start=1):
        task = by_id.get(item.get("id")) or {}
        line.append({
            "position": position,
            "id": item.get("id"),
            "title": task.get("title", ""),
            "marker": KIND_MARKERS.get(item.get("kind") or task.get("kind", ""), KIND_MARKER_FALLBACK),
            "state": item.get("state"),
            "priority": item.get("priority"),
            "pr": item.get("pr"),
            "enqueuedAt": item.get("enqueuedAt"),
            "approved": bool(item.get("approval")),
            "audited": bool(item.get("auditedSha")),
            "dependsOn": item.get("dependsOn") or [],
            "waiting": reason,
            "ready": reason is None and item.get("state") in OPEN_STATES,
        })
    nxt = next((entry for entry in line if entry["ready"]), None)
    for entry in line:
        entry["next"] = entry is nxt
    history = [h for h in data.get("history") or [] if isinstance(h, dict)][-QUEUE_HISTORY_LIMIT:]
    return {
        "paused": bool(data.get("paused")),
        "pausedReason": data.get("pausedReason"),
        "frozenReason": data.get("frozenReason"),
        "stopped": queue_stopped(data),
        "executor": _executor(root, config, time.time()),
        "items": line,
        "head": line[0] if line else None,
        "next": nxt,
        "history": [
            {"id": h.get("id"), "state": h.get("state"), "pr": h.get("pr"), "closedAt": h.get("closedAt"), "reason": h.get("reason")}
            for h in reversed(history)
        ],
    }


def engine_for(root: Path) -> Path:
    """O motor que os botoes do painel rodam no projeto (D-187): o do proprio
    projeto quando ele tem um; senao o do painel. Um painel aberto de outra
    versao nao integra PRs com o codigo dela."""
    return next((root / rel for rel in PROJECT_ENGINES if (root / rel).is_file()), ENGINE)


def _engine(root: Path) -> dict[str, Any]:
    """D-195: o motor que o botao rodaria, para o confirm mostrar. `own`
    quando o script vem da pasta do projeto - e quem o controla e o projeto
    (um clone de terceiro achado por --scan), nao o Guia que serve o painel."""
    path = engine_for(root)
    own = os.path.normcase(str(path.resolve())) != os.path.normcase(str(ENGINE))
    return {"path": str(path), "own": own}


def snapshot(root: Path) -> dict[str, Any]:
    """Tudo o que o painel mostra de um projeto, lido do `.guia/` dele."""
    guia = root / ".guia"
    config = _read(guia / "process.json", {})
    config = config if isinstance(config, dict) else {}
    tasks_doc = _read(guia / "tasks.json", {})
    tasks = [t for t in (tasks_doc.get("tasks") if isinstance(tasks_doc, dict) else None) or [] if isinstance(t, dict) and t.get("id")]
    by_id = {t["id"]: t for t in tasks}
    columns: dict[str, list[dict[str, Any]]] = {key: [] for key, _ in STAGES}
    done: list[dict[str, Any]] = []
    for task in tasks:
        card = _card(task, config)
        if card["status"] in columns:
            columns[card["status"]].append(card)
        elif card["status"] in DONE_STATUSES:
            done.append(card)
    for cards in columns.values():
        cards.sort(key=lambda c: c.get("updatedAt") or "", reverse=True)
    done.sort(key=lambda c: (c.get("finishedAt") or c.get("updatedAt") or "", c["id"] or ""), reverse=True)
    current = _read(guia / "current-task.json", {})
    delivery = config.get("delivery") if isinstance(config.get("delivery"), dict) else {}
    return {
        "path": str(root),
        "name": config.get("projectName") or config.get("name") or root.name,
        "mode": delivery.get("mode") or "direct",
        "current": current.get("taskId") if isinstance(current, dict) else None,
        "stages": [{"key": key, "label": label, "cards": columns[key]} for key, label in STAGES],
        "counts": {key: len(columns[key]) for key, _ in STAGES},
        "active": sum(len(columns[key]) for key, _ in STAGES if key != "Backlog"),
        "recentDone": done[:RECENT_DONE_LIMIT],
        "doneTotal": len(done),
        "queue": _queue(root, by_id, config),
        "engine": _engine(root),
    }


def engine_version(engine_dir: Path | None = None) -> dict[str, Any]:
    """A versao do Guia que serve o painel (D-192), lida ao lado do motor em
    uso: no repo-mae `core/src/` -> `VERSION` da raiz; no plugin instalado
    `bin/` -> `.claude-plugin/plugin.json`. Sem achar, `version` fica None."""
    here = engine_dir or Path(__file__).resolve().parent
    version_file = here.parent.parent / "VERSION"
    if here.name == "src" and version_file.is_file():
        try:
            return {"version": version_file.read_text(encoding="utf-8").strip() or None, "source": "VERSION", "engine": str(here)}
        except OSError:
            pass
    manifest = _read(here.parent / ".claude-plugin" / "plugin.json", {})
    version = manifest.get("version") if isinstance(manifest, dict) else None
    return {"version": version if isinstance(version, str) else None, "source": "plugin.json" if version else None, "engine": str(here)}


def overview(paths: list[str]) -> dict[str, Any]:
    """Retrato de todos os projetos cadastrados; um projeto sumido ou com
    estado ilegivel vira um aviso no card, sem derrubar o painel."""
    projects = []
    for raw in paths:
        root = Path(raw)
        if not is_project(root):
            projects.append({"path": raw, "name": root.name, "error": "pasta sem .guia/tasks.json (movida ou apagada?)"})
            continue
        try:
            projects.append(snapshot(root))
        except Exception as exc:  # noqa: BLE001 - o painel nao cai por um projeto
            projects.append({"path": raw, "name": root.name, "error": f"{type(exc).__name__}: {exc}"})
    return {"projects": projects, "guia": engine_version()}


__all__ = [
    "STAGES",
    "add_projects",
    "engine_for",
    "engine_version",
    "is_project",
    "load_projects",
    "overview",
    "queue_stopped",
    "registry_file",
    "remove_project",
    "scan",
    "snapshot",
]
