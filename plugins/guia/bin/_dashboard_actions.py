"""Acoes do painel (D-187): retomar a fila e iniciar o executor de um projeto.

As duas unicas escritas do painel, e nenhuma delas e escrita do painel: cada
acao roda o motor dentro do projeto (`GUIA_PROJECT_ROOT` apontando para
ele; o motor do proprio projeto quando ele tem um, senao o do painel), entao
o estado continua mudando so pelo script. O painel decide
apenas se a acao faz sentido agora, pelo mesmo retrato que mostra na tela.

- `resume`: `queue resume`, curto, em primeiro plano; devolve a saida.
- `start_executor`: `queue run` em processo destacado (sobrevive ao painel).
  O executor pega o lease com batimento (D-127) - o `O_EXCL` do lease e a
  garantia de um executor por repositorio; aqui so evitamos o clique que
  ja nasceria recusado (executor vivo, ou um iniciado pelo painel que ainda
  nao gravou o lease).

Quem dispara e o dono, num clique no navegador; a protecao contra pedido
forjado (token, Origin, Host) mora no servidor (`_cli_dashboard`).
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

from _dashboard import ENGINE, PROJECT_ENGINES, engine_for, is_project, load_projects, queue_stopped, snapshot
EXECUTOR_LOG = Path(".guia") / "queue" / "executor-painel.log"
RESUME_TIMEOUT_SECONDS = 60

_spawn_lock = threading.Lock()
_spawned: dict[str, subprocess.Popen[bytes]] = {}


class ActionError(Exception):
    """Pedido recusado; `status` e o codigo HTTP que o servidor devolve."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


def _key(path: str) -> str:
    return os.path.normcase(str(Path(path).resolve()))


def registered_project(raw: Any) -> Path:
    """So projeto do cadastro: o pedido nunca escolhe uma pasta qualquer."""
    if not isinstance(raw, str) or not raw:
        raise ActionError(400, "informe o projeto")
    wanted = _key(raw)
    for path in load_projects():
        if _key(path) == wanted:
            root = Path(path)
            if not is_project(root):
                raise ActionError(404, f"{path} nao tem mais .guia/tasks.json")
            return root
    raise ActionError(404, "projeto fora do cadastro do painel")


def _engine_env(root: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["GUIA_PROJECT_ROOT"] = str(root)
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def resume(root: Path) -> str:
    queue = snapshot(root)["queue"]
    if not queue_stopped(queue):
        raise ActionError(409, "a fila nao esta pausada")
    result = subprocess.run(
        [sys.executable, str(engine_for(root)), "queue", "resume"],
        cwd=root, env=_engine_env(root), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=RESUME_TIMEOUT_SECONDS,
    )
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        raise ActionError(500, output or f"queue resume saiu com {result.returncode}")
    return output


def _detach_kwargs() -> dict[str, Any]:
    if os.name == "nt":
        # Console proprio e escondido: sem console (DETACHED_PROCESS), cada
        # git/gh/pytest que o executor chama abriria uma janela visivel.
        # Grupo proprio: o Ctrl+C do painel nao chega ao executor.
        flags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
        return {"creationflags": flags}
    return {"start_new_session": True}


def _refuse_start(snap: dict[str, Any]) -> None:
    """O que o retrato ja diz contra iniciar: sem fila, fila parada, executor vivo."""
    if snap["mode"] != "pr":
        raise ActionError(409, "projeto sem entrega por PR: nao ha fila para o executor")
    queue = snap["queue"]
    if queue_stopped(queue):
        raise ActionError(409, "a fila esta parada: retome antes de iniciar o executor")
    executor = queue["executor"]
    if executor and executor["alive"]:
        raise ActionError(409, f"executor ja ativo (pid {executor['pid']} em {executor['host']})")


def start_executor(root: Path) -> str:
    _refuse_start(snapshot(root))
    key = _key(str(root))
    with _spawn_lock:
        previous = _spawned.get(key)
        if previous is not None and previous.poll() is None:
            raise ActionError(409, f"executor iniciado pelo painel ainda rodando (pid {previous.pid})")
        log_path = root / EXECUTOR_LOG
        log_path.parent.mkdir(parents=True, exist_ok=True)
        engine = engine_for(root)
        with open(log_path, "ab") as log:
            process = subprocess.Popen(
                [sys.executable, str(engine), "queue", "run"],
                cwd=root, env=_engine_env(root), stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, close_fds=True, **_detach_kwargs(),
            )
        _spawned[key] = process
    return f"Executor iniciado (pid {process.pid}, motor {engine}); saida em {EXECUTOR_LOG.as_posix()}."


ACTIONS = {"queue-resume": resume, "queue-run": start_executor}


__all__ = ["ACTIONS", "ENGINE", "PROJECT_ENGINES", "ActionError", "engine_for", "registered_project", "resume", "start_executor"]
