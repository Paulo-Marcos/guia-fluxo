"""CLI handlers: queue e approve (D-126)."""

from __future__ import annotations

import argparse
import json
from typing import Any

from _autonomy import effective_level, human_reasons, implicit_approval, rank
from _clock import now_iso
from _conductor import announce_next
from _constants import DELIVERY_BASE_BRANCH_DEFAULT, PROCESS_FILE, ROOT, STATUS_IN_PR, STATUS_IN_QUEUE
from _git_ops import git_output
from _github import gh_pr_state
from _state import read_json
from _dependabot import lote_human_reasons
from _merge_queue import PRIORITY_HOTFIX, PRIORITY_NORMAL, STATE_CONFLICT, STATE_WAITING, find, load, mutate, ordered
from _ship import QUEUE_DIR
from _tasks import find_task, find_task_or_current, save_task


def _status_of(task_id: str) -> str | None:
    task = find_task(task_id)
    return task.get("status") if task else None


def _pr_changed_paths(pr: dict[str, Any], config: dict[str, Any]) -> list[str] | None:
    """Arquivos que o PR muda, pelo git (D-134): nunca pela lista declarada."""
    base = (config.get("delivery") or {}).get("baseBranch") or DELIVERY_BASE_BRANCH_DEFAULT
    branch = pr.get("branch")
    if not branch:
        return None
    git_output(ROOT, "fetch", "-q", "origin", base, branch)
    names = git_output(ROOT, "diff", "--name-only", f"origin/{base}...origin/{branch}")
    return None if names is None else [line for line in names.splitlines() if line.strip()]


def _live_head(pr: dict[str, Any]) -> str | None:
    """Head do PR no GitHub agora (D-162); None sem `gh` (vale o gravado)."""
    try:
        return gh_pr_state(ROOT, pr["number"]).get("head")
    except SystemExit:
        return None


def _enqueue(args: argparse.Namespace) -> int:
    task = find_task_or_current(args.task_id)
    pr = task.get("pr") or {}
    audit = task.get("audit") or {}
    message = QUEUE_DIR / f"{task['id']}.msg"
    if not pr.get("number"):
        raise SystemExit(f"{task['id']} sem PR: rode `guia ship` antes.")
    if audit.get("result") != "approved":
        raise SystemExit(f"{task['id']} sem auditoria aprovada: rode `guia audit --report ... --approve`.")
    # D-162: rebase + push fora do `ship` deixa o `pr.head` gravado para tras;
    # a auditoria vale contra o head que o PR tem AGORA, e o registro o segue.
    pr["head"] = _live_head(pr) or pr.get("head")
    if audit.get("auditedSha") != pr.get("head"):
        raise SystemExit(
            f"A auditoria e do head {audit.get('auditedSha')}, mas o PR esta em {pr.get('head')}: "
            "audite o head novo antes de enfileirar."
        )
    if not message.is_file():
        raise SystemExit(f"Sem a mensagem de squash {message}: rode `guia ship` de novo.")
    config = read_json(PROCESS_FILE, {})
    reasons: list[str] = []
    approval = None
    level = effective_level(task, config)
    if rank(level) >= rank("queue"):
        # D-134: so com autonomia para aprovar sozinho faz sentido conferir o
        # alwaysHuman; abaixo disso o item espera o approve de qualquer jeito.
        if task.get("dependabot") and level == "pilot":
            # D-150: no pilot, o lote so para no dono no que vai alem de versao.
            base = (config.get("delivery") or {}).get("baseBranch") or DELIVERY_BASE_BRANCH_DEFAULT
            reasons = lote_human_reasons(task, base, pr.get("branch"), config)
        else:
            reasons = human_reasons(_pr_changed_paths(pr, config), message.read_text(encoding="utf-8"), config)
        approval = implicit_approval(task, config, reasons)
    priority = args.priority
    if (task.get("dependabot") or {}).get("security"):
        priority = PRIORITY_HOTFIX  # D-150: atualizacao de seguranca passa a frente

    def add(data: dict[str, Any]) -> None:
        existing = find(data, task["id"])
        if existing and existing.get("state") == STATE_CONFLICT:
            # D-164: o gerente resolveu - o item volta a esperar no mesmo lugar.
            # A aprovacao do dono so fica se a resolucao nao trouxe nada sensivel novo.
            kept = (existing.get("approval") or {}).get("by") == "user" and existing.get("humanReason") == ("; ".join(reasons) or None)
            existing.update(auditedSha=audit["auditedSha"], auditedPatchId=audit.get("auditedPatchId"), head=pr.get("head"),
                            mergeMessageFile=message.relative_to(QUEUE_DIR.parent.parent).as_posix(), state=STATE_WAITING,
                            conflictReason=None, approval=approval or (existing.get("approval") if kept else None),
                            humanReason="; ".join(reasons) or None)
            existing.setdefault("log", []).append({"at": now_iso(), "msg": "conflito resolvido pelo gerente; de volta a fila"})
            return
        if existing and not existing.get("auditedSha"):
            # D-130: item importado da nuvem - a auditoria do PC o completa.
            existing.update(auditedSha=audit["auditedSha"], auditedPatchId=audit.get("auditedPatchId"),
                            head=pr.get("head"), mergeMessageFile=message.relative_to(QUEUE_DIR.parent.parent).as_posix())
            existing.setdefault("log", []).append({"at": now_iso(), "msg": "auditoria do PC registrada"})
            return
        if existing:
            raise SystemExit(f"{task['id']} ja esta na fila.")
        data["items"].append({
            "id": task["id"],
            "kind": task.get("kind"),
            "pr": pr["number"],
            "branch": pr.get("branch"),
            "worktree": (task.get("worktree") or {}).get("path"),
            "enqueuedAt": now_iso(),
            "enqueuedBy": "chat",
            "priority": priority,
            "dependsOn": list(task.get("dependsOn") or []),
            "auditedSha": audit["auditedSha"],
            "auditedPatchId": audit.get("auditedPatchId"),
            "approval": approval,
            "humanReason": "; ".join(reasons) or None,
            "mergeMessageFile": message.relative_to(QUEUE_DIR.parent.parent).as_posix(),
            "state": STATE_WAITING,
            "attempts": 0,
            "log": [],
        })

    mutate(add)
    task["status"] = STATUS_IN_QUEUE
    save_task(task)
    print(f"{task['id']} na fila (PR #{pr['number']}, prioridade {priority}).")
    if approval:
        print(f"Aprovado pela autonomia (nivel {approval['level']}): o executor integra sem novo ok.")
    elif reasons:
        print(f"alwaysHuman: espera o approve do dono - {'; '.join(reasons)}.")
    announce_next(task, config)
    return 0


def _list(args: argparse.Namespace) -> int:
    data = load()
    rows = [
        {"id": item["id"], "pr": item.get("pr"), "priority": item.get("priority"),
         "state": item.get("state"), "waiting": why}
        for item, why in ordered(data["items"], _status_of)
    ]
    if args.json:
        print(json.dumps({"paused": data["paused"], "pausedReason": data.get("pausedReason"),
                          "frozenReason": data.get("frozenReason"), "items": rows}, ensure_ascii=False, indent=2))
        return 0
    if data["paused"]:
        print(f"Fila PAUSADA: {data.get('pausedReason') or 'sem motivo'}")
    if data.get("frozenReason"):
        print(f"Fila CONGELADA: {data['frozenReason']}")
    if not rows:
        print("Fila vazia.")
    for position, row in enumerate(rows, start=1):
        flag = " [hotfix]" if row["priority"] == "hotfix" else ""
        print(f"{position}. {row['id']} PR #{row['pr']}{flag} - {row['waiting'] or 'pronto para integrar'}")
    return 0


def _remove(args: argparse.Namespace) -> int:
    def drop(data: dict[str, Any]) -> None:
        item = find(data, args.task_id)
        if not item:
            raise SystemExit(f"{args.task_id} nao esta na fila.")
        data["items"].remove(item)

    mutate(drop)
    task = find_task(args.task_id)
    if task and task.get("status") == STATUS_IN_QUEUE:
        task["status"] = STATUS_IN_PR
        save_task(task)
    print(f"{args.task_id} saiu da fila.")
    return 0


def _set_paused(paused: bool, reason: str | None) -> int:
    def change(data: dict[str, Any]) -> str | None:
        data["paused"] = paused
        data["pausedReason"] = reason if paused else None
        frozen = data.get("frozenReason")
        if not paused:
            # D-128: retomar tambem descongela - decisao do dono, depois de a
            # main voltar ao verde.
            data["frozenReason"] = None
        return frozen

    frozen = mutate(change)
    print("Fila pausada." if paused else "Fila retomada." + (f" Estava congelada: {frozen}" if frozen else ""))
    return 0


def _priority(args: argparse.Namespace) -> int:
    def change(data: dict[str, Any]) -> None:
        item = find(data, args.task_id)
        if not item:
            raise SystemExit(f"{args.task_id} nao esta na fila.")
        item["priority"] = args.level

    mutate(change)
    print(f"{args.task_id}: prioridade {args.level}.")
    return 0


def _run(args: argparse.Namespace) -> int:
    from _executor import run  # import tardio: so o `run` precisa do executor
    from _state import read_json
    from _constants import PROCESS_FILE

    merged = run(read_json(PROCESS_FILE, {}), once=args.once)
    print(f"Executor: {merged} PR(s) integrado(s).")
    return 0


def _import(_args: argparse.Namespace) -> int:
    from _cloud_import import import_labeled

    imported, warnings = import_labeled()
    for warning in warnings:
        print(f"aviso: {warning}")
    print(f"Importados da nuvem: {', '.join(imported) or 'nenhum'}")
    return 0


def cmd_queue(args: argparse.Namespace) -> int:
    action = args.action or "list"
    if action == "import":
        return _import(args)
    if action == "run":
        return _run(args)
    if action == "add":
        return _enqueue(args)
    if action == "remove":
        return _remove(args)
    if action in ("pause", "resume"):
        return _set_paused(action == "pause", args.reason)
    if action == "priority":
        return _priority(args)
    return _list(args)


def cmd_approve(args: argparse.Namespace) -> int:
    """Ok de merge (acao do usuario, como o finish): libera itens para o executor."""
    if not args.all and not args.task_ids:
        raise SystemExit("Passe os ids (approve D-NNN ...) ou --all.")

    def change(data: dict[str, Any]) -> list[str]:
        approved = []
        for item in data["items"]:
            if item.get("state") == STATE_WAITING and (args.all or item["id"] in args.task_ids):
                item["approval"] = {"by": "user", "at": now_iso()}
                approved.append(item["id"])
        return approved

    approved = mutate(change)
    print(f"Aprovados: {', '.join(approved) or 'nenhum'}")
    return 0


__all__ = ["PRIORITY_NORMAL", "cmd_approve", "cmd_queue"]
