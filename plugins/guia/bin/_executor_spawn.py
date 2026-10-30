"""Subir o executor da fila destacado (D-187, D-204), sem o painel.

Dois clientes: o botao do painel (`_dashboard_actions.start_executor`) e o
proprio chat no `pilot` (D-204), que no `queue add` garante que alguem vai
integrar. Quem garante UM executor por repositorio e o lease com `O_EXCL`
(D-127, `_executor.acquire_lease`): dois chats que sobem ao mesmo tempo
deixam o segundo `queue run` recusado no log, nunca dois integrando.

A ordem fecha a corrida com o executor que esta saindo: quem enfileira grava
o item e SO DEPOIS le o lease; o executor solta o lease e SO DEPOIS rele a
fila (`_executor.run`). Um dos dois sempre ve o outro.

Modulo leve (sem git/gh): o `queue add` e o `next` o importam.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from _autonomy import effective_level
from _constants import ROOT
from _lease import executor_status
from _merge_queue import STATE_CONFLICT, find, load

ENGINE = Path(__file__).resolve().parent / "guia.py"
# Motor que mora dentro do projeto (repo-mae, dogfood, copia manual). Sem
# nenhum (o caso do plugin), vale o que esta rodando.
PROJECT_ENGINES = (Path("core/src/guia.py"), Path("plugins/guia/bin/guia.py"), Path(".guia-fluxo/bin/guia.py"))
AUTO_LOG = Path(".guia") / "queue" / "executor-auto.log"
# Quando o chat subiu um executor: `next` logo depois do `queue add` nao sobe
# outro enquanto o primeiro ainda carrega e nao gravou o lease.
SPAWN_MARK = Path(".guia") / "queue" / "executor-auto.spawned"
SPAWN_GRACE_SECONDS = 20.0
AUTO_LEVEL = "pilot"  # D-204: o dono decidiu que o pilot ja autoriza o chat a ligar a fila
# Desliga o spawn automatico (o conftest dos testes usa: nenhum teste sobe um
# executor destacado por acaso). Nao e autorizacao: abaixo do pilot nada sobe.
AUTO_SWITCH_ENV = "GUIA_AUTO_EXECUTOR"


def engine_for(root: Path) -> Path:
    """O motor do proprio projeto quando ele tem um; senao o que esta rodando.

    O executor remove o worktree da demanda no meio da passada (D-137): o
    motor sai da arvore principal (`root`), nunca do worktree de quem pediu.
    """
    return next((root / rel for rel in PROJECT_ENGINES if (root / rel).is_file()), ENGINE)


def detach_kwargs() -> dict[str, Any]:
    if os.name == "nt":
        # Console proprio e escondido: sem console (DETACHED_PROCESS), cada
        # git/gh/pytest que o executor chama abriria uma janela visivel.
        # Grupo proprio: o Ctrl+C de quem subiu nao chega ao executor.
        flags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
        return {"creationflags": flags}
    return {"start_new_session": True}


def spawn_executor(root: Path, log: Path) -> tuple[subprocess.Popen[bytes], Path]:
    """`queue run` em processo destacado, com a saida em `root/log`."""
    log_path = root / log
    log_path.parent.mkdir(parents=True, exist_ok=True)
    engine = engine_for(root)
    env = {**os.environ, "GUIA_PROJECT_ROOT": str(root), "PYTHONIOENCODING": "utf-8"}
    with open(log_path, "ab") as out:
        process = subprocess.Popen(
            [sys.executable, str(engine), "queue", "run"],
            cwd=root, env=env, stdin=subprocess.DEVNULL,
            stdout=out, stderr=subprocess.STDOUT, close_fds=True, **detach_kwargs(),
        )
    return process, engine


def _why_not(task: dict[str, Any]) -> str | None:
    """Por que a fila nao tem o que integrar deste item agora; None quando tem."""
    data = load()
    if data.get("paused") or data.get("frozenReason"):
        return f"fila parada ({data.get('pausedReason') or data.get('frozenReason')}): o dono retoma"
    item = find(data, task["id"])
    if item is None or item.get("state") == STATE_CONFLICT or not item.get("approval"):
        return "o item nao esta na fila aprovado: o executor nao teria o que integrar"
    return None


def ensure_executor(task: dict[str, Any], config: dict[str, Any]) -> str | None:
    """D-204: no pilot, garante um executor vivo depois do item gravado na fila.

    Devolve a linha para o chat, ou None quando nao se aplica (abaixo do
    pilot o texto do condutor ja diz que a fila e do dono). Idempotente:
    executor vivo -> nada; sem lease -> sobe um.
    """
    if os.environ.get(AUTO_SWITCH_ENV, "").lower() in ("0", "off", "false"):
        return None
    if effective_level(task, config) != AUTO_LEVEL:
        return None
    why = _why_not(task)
    if why is not None:
        return f"Executor nao ligado: {why}."
    alive = executor_status(config)
    if alive:
        return f"Executor ja ativo (pid {alive['pid']} em {alive['host']}): ele integra este item."
    mark = ROOT / SPAWN_MARK
    try:
        age = time.time() - mark.stat().st_mtime
    except OSError:
        age = None
    if age is not None and age < SPAWN_GRACE_SECONDS:
        return f"Executor ligado ha {age:.0f}s, ainda subindo: ele integra este item."
    process, engine = spawn_executor(ROOT, AUTO_LOG)
    mark.write_text(str(process.pid), encoding="utf-8")
    return (f"Executor ligado pelo pilot (pid {process.pid}, motor {engine}); "
            f"saida em {AUTO_LOG.as_posix()}.")


__all__ = ["AUTO_LEVEL", "AUTO_LOG", "AUTO_SWITCH_ENV", "ENGINE", "PROJECT_ENGINES", "detach_kwargs", "engine_for", "ensure_executor", "spawn_executor"]
