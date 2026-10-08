"""O executor da fila (D-127, R5 + R8): integra um PR por vez, sem LLM.

Mecanica pura no motor - mecanica feita por agente erra de jeito novo a cada
vez. Um executor por repositorio (lease com batimento). Por item elegivel:

1. le o PR: mergeado por fora reconcilia; fechado devolve;
2. head x auditoria: patch-id igual carrega o marcador (R8), diferente devolve;
3. BEHIND -> update-branch --rebase; conflito devolve; head novo volta ao 2;
4. espera os checks exigidos: vermelho devolve; estouro do tempo deixa esperando;
5. merge --squash --match-head-commit com a mensagem da fila -> Integrada.

Devolver tira o item da fila, volta a demanda a `Em desenvolvimento` com o
motivo, e o executor segue: um PR problematico nao segura a fila.
"""

from __future__ import annotations

import json
import os
import socket
import time
from pathlib import Path
from typing import Any

from _clock import now_iso
from _constants import (
    DELIVERY_BASE_BRANCH_DEFAULT,
    GUIA_DIR,
    ROOT,
    STATUS_IN_DEVELOPMENT,
    STATUS_INTEGRATED,
)
from _github import (
    gh_pr_checks,
    gh_pr_comment,
    gh_pr_merge,
    gh_pr_state,
    gh_pr_update_branch,
    pr_patch_id,
)
from _merge_queue import find, load, mutate, ordered
from _tasks import find_task, save_task

LEASE_FILE = GUIA_DIR / "queue" / "executor.lease"
LEASE_STALE_MINUTES_DEFAULT = 10
CI_TIMEOUT_MINUTES_DEFAULT = 40


class Returned(Exception):
    """O item volta ao autor com este motivo."""


# --- lease -----------------------------------------------------------------


def _read_lease() -> dict[str, Any] | None:
    try:
        return json.loads(LEASE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def acquire_lease(stale_minutes: float) -> None:
    LEASE_FILE.parent.mkdir(parents=True, exist_ok=True)
    me = {"pid": os.getpid(), "host": socket.gethostname(), "startedAt": now_iso(), "heartbeat": time.time()}
    while True:
        try:
            fd = os.open(LEASE_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            holder = _read_lease() or {}
            age = time.time() - float(holder.get("heartbeat") or 0)
            if age < stale_minutes * 60:
                raise SystemExit(
                    f"Executor ja rodando: pid {holder.get('pid')} em {holder.get('host')} "
                    f"(batimento ha {age:.0f}s). Um executor por repositorio."
                )
            LEASE_FILE.unlink(missing_ok=True)
            continue
        os.write(fd, json.dumps(me).encode("utf-8"))
        os.close(fd)
        return


def heartbeat() -> None:
    lease = _read_lease()
    if lease and lease.get("pid") == os.getpid():
        lease["heartbeat"] = time.time()
        LEASE_FILE.write_text(json.dumps(lease), encoding="utf-8")


def release_lease() -> None:
    lease = _read_lease()
    if lease and lease.get("pid") == os.getpid():
        LEASE_FILE.unlink(missing_ok=True)


# --- passos ----------------------------------------------------------------


def _log(item_id: str, message: str) -> None:
    def append(data: dict[str, Any]) -> None:
        item = find(data, item_id)
        if item is not None:
            item.setdefault("log", []).append({"at": now_iso(), "msg": message})

    mutate(append)
    print(f"  {item_id}: {message}")


def _carry_or_return(item: dict[str, Any], head: str, base: str) -> None:
    """R8: head diferente do auditado so segue se o conteudo (patch-id) for o mesmo."""
    if head == item["auditedSha"]:
        return
    patch = pr_patch_id(ROOT, item["pr"], head, base)
    if not patch or patch != item.get("auditedPatchId"):
        raise Returned(f"o PR mudou depois da auditoria (head {head[:12]}, patch-id diferente): audite o head novo")
    gh_pr_comment(ROOT, item["pr"], (
        f"Auditoria carregada pelo executor do Guia: rebase limpo, mesmo conteudo.\n"
        f"carry-from={item['auditedSha']} patch-id={patch}\n\n"
        f"<!-- auditoria-aprovada sha={head} -->\n"
    ))

    def update(data: dict[str, Any]) -> None:
        current = find(data, item["id"])
        if current is not None:
            current["auditedSha"] = head

    mutate(update)
    item["auditedSha"] = head
    _log(item["id"], f"auditoria carregada para {head[:12]} (patch-id {patch[:12]})")


def _merge_message(item: dict[str, Any]) -> tuple[str, str]:
    text = (ROOT / item["mergeMessageFile"]).read_text(encoding="utf-8")
    subject, _sep, body = text.partition("\n")
    return f"{subject.strip()} (#{item['pr']})", body.strip() + "\n"


def integrate(item: dict[str, Any], base: str, ci_timeout_seconds: float) -> str:
    """Leva um item ate o merge; devolve 'merged' ou 'waiting'. Levanta Returned."""
    state = gh_pr_state(ROOT, item["pr"])
    if state["state"] == "MERGED":
        return "merged"
    if state["state"] != "OPEN":
        raise Returned(f"PR #{item['pr']} esta {state['state']} sem merge")
    head = state["head"]
    _carry_or_return(item, head, base)
    if state["mergeState"] == "DIRTY":
        raise Returned("conflito com a base: resolva na branch (rebase) e rode o ship")
    if state["mergeState"] == "BEHIND":
        new_head, error = gh_pr_update_branch(ROOT, item["pr"])
        if error:
            raise Returned(f"conflito ao atualizar a branch: {error}")
        _log(item["id"], f"branch atualizada: {head[:12]} -> {new_head[:12]}")
        head = new_head
        _carry_or_return(item, head, base)
    heartbeat()
    verdict, failing = gh_pr_checks(ROOT, item["pr"], ci_timeout_seconds)
    if verdict == "fail":
        raise Returned(f"check vermelho: {', '.join(failing)}")
    if verdict != "pass":
        _log(item["id"], "checks ainda pendentes no tempo limite; fica esperando")
        return "waiting"
    subject, body = _merge_message(item)
    error = gh_pr_merge(ROOT, item["pr"], head, subject, body)
    if error:
        raise Returned(f"merge recusado: {error}")
    item["mergedHead"] = head
    return "merged"


def _finish_item(item: dict[str, Any], outcome: str, reason: str | None = None) -> None:
    def drop(data: dict[str, Any]) -> None:
        current = find(data, item["id"])
        if current is not None:
            data["items"].remove(current)
            data.setdefault("history", []).append({**current, "state": outcome, "closedAt": now_iso(), "reason": reason})

    mutate(drop)
    task = find_task(item["id"])
    if task is None:
        return
    if outcome == "merged":
        task["status"] = STATUS_INTEGRATED
        task.setdefault("pr", {})["mergedAt"] = now_iso()
        print(f"{item['id']}: integrada (PR #{item['pr']}).")
    else:
        task["status"] = STATUS_IN_DEVELOPMENT
        queue = task.setdefault("queue", {})
        queue.update(returnReason=reason, returnedAt=now_iso())
        queue["returnCount"] = queue.get("returnCount", 0) + 1
        print(f"{item['id']}: DEVOLVIDA - {reason}")
    save_task(task)


def run(config: dict[str, Any], once: bool = False) -> int:
    """Uma passada pela fila; devolve quantos itens foram integrados."""
    delivery = config.get("delivery") or {}
    queue_cfg = delivery.get("queue") or {}
    base = delivery.get("baseBranch") or DELIVERY_BASE_BRANCH_DEFAULT
    ci_timeout = float(queue_cfg.get("ciTimeoutMinutes") or CI_TIMEOUT_MINUTES_DEFAULT) * 60
    acquire_lease(float(queue_cfg.get("leaseStaleMinutes") or LEASE_STALE_MINUTES_DEFAULT))
    merged = 0
    tried: set[str] = set()
    try:
        while True:
            data = load()
            if data["paused"] or data.get("frozenReason"):
                print(f"Fila parada: {data.get('pausedReason') or data.get('frozenReason')}")
                break
            status_of = lambda task_id: (find_task(task_id) or {}).get("status")  # noqa: E731
            eligible = [item for item, why in ordered(data["items"], status_of) if why is None and item["id"] not in tried]
            if not eligible:
                break
            item = eligible[0]
            tried.add(item["id"])
            print(f"Integrando {item['id']} (PR #{item['pr']})...")
            heartbeat()
            try:
                outcome = integrate(item, base, ci_timeout)
            except Returned as reason:
                _finish_item(item, "returned", str(reason))
                continue
            if outcome == "merged":
                _finish_item(item, "merged")
                merged += 1
                if once:
                    break
    finally:
        release_lease()
    return merged


__all__ = ["LEASE_FILE", "Returned", "acquire_lease", "integrate", "release_lease", "run"]
