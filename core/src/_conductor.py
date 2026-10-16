"""O condutor (D-152, epico E-009): o proximo passo da demanda, decidido pelo motor.

Depois do `ready`, o nivel de autonomia conduz a demanda ate onde pode. Quem
decide o passo e o motor - o agente executa o que `guia next` manda e repete
ate ouvir `stop` ou `done`, sem improvisar o fluxo. As regras do Guia
(auditoria no head atual, alwaysHuman, R7, o nivel) ficam aqui, testadas:

    manual  ready e para
    pr      + ship + auditoria
    queue   + entra na fila (aprovada se nada e sensivel)
    pilot   + idem - a fila (queue run) integra, limpa e fecha quando a R7 deixa

O chat vai ate o `queue add` e encerra: integrar e da fila, um processo a
parte. `stop` sempre vem com o motivo e com quem destrava (dono, agente, fila).
"""

from __future__ import annotations

from typing import Any

from _autonomy import effective_level, rank
from _constants import (
    DELIVERY_MODE_DIRECT,
    DELIVERY_MODE_PR,
    STATUS_AWAITING_VALIDATION,
    STATUS_AWAITING_VALIDATION_ACCENTED,
    STATUS_IN_DEVELOPMENT,
    STATUS_IN_PR,
    STATUS_IN_QUEUE,
    STATUS_INTEGRATED,
)
from _lease import describe_executor
from _merge_queue import find, load

STEP_READY, STEP_SHIP, STEP_AUDIT = "ready", "ship", "audit"
STEP_QUEUE_ADD = "queue-add"
STEP_STOP, STEP_DONE = "stop", "done"
_AWAITING = (STATUS_AWAITING_VALIDATION, STATUS_AWAITING_VALIDATION_ACCENTED)


def _step(step: str, why: str, level: str, owner: str | None = None) -> dict[str, Any]:
    return {"step": step, "why": why, "level": level, "owner": owner}


def _stop(why: str, level: str, owner: str = "dono") -> dict[str, Any]:
    return _step(STEP_STOP, why, level, owner)


def _after_ready(task: dict[str, Any], level: str, mode: str) -> dict[str, Any]:
    if mode != DELIVERY_MODE_PR:
        return _stop("modo direct: sem PR - valide e decida o finish", level)
    if rank(level) < rank("pr"):
        return _stop("nivel manual: valide e decida o finish", level)
    from _legacy_ready import legacy_ready  # D-180: lido so aqui, apos o ready

    first_pr = legacy_ready(task)
    if first_pr:
        return _stop(f"legado: ready antes do primeiro PR do projeto ({first_pr[:10]}), o codigo ja entrou direto "
                     "na base - valide e decida o finish ou o cancel", level)
    return _step(STEP_SHIP, "pronta: portao, push e PR", level)


def _in_pr(task: dict[str, Any], level: str) -> dict[str, Any]:
    pr, audit = task.get("pr") or {}, task.get("audit") or {}
    if audit.get("auditedSha") != pr.get("head"):
        return _step(STEP_AUDIT, "o head do PR ainda nao foi auditado", level)
    if audit.get("result") != "approved":
        return _stop("auditoria reprovou: corrija os achados na branch e rode o ship", level, "agente")
    if rank(level) < rank("queue"):
        return _stop("nivel pr: entrar na fila e do dono (queue add + approve)", level)
    return _step(STEP_QUEUE_ADD, "auditada no head atual", level)


def _in_queue(task: dict[str, Any], level: str, config: dict[str, Any]) -> dict[str, Any]:
    item = find(load(), task["id"])
    if item is None:
        return _stop("status Na fila, mas fora da fila: rode `guia queue` e confira", level)
    if not item.get("approval"):
        reason = item.get("humanReason") or "sem aprovacao de merge"
        return _stop(f"aguarda o approve do dono ({reason})", level)
    # D-176: o chat sabe se ha executor vivo - com ele, o queue add e o fim.
    return _stop(f"na fila e aprovada; {describe_executor(config)}", level, "fila")


def _integrated(task: dict[str, Any], level: str) -> dict[str, Any]:
    failed = [c for c in (task.get("autoFinish") or {}).get("checks") or [] if not c.get("ok")]
    if failed:
        why = "; ".join(f"{c['check']}: {c['evidence']}" for c in failed)
        return _stop(f"integrada; fechar e do dono ({why})", level)
    return _stop("integrada; valide no uso e rode o finish", level)


def next_step(task: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """O proximo passo da demanda segundo o estado, o nivel e a fila (com o chat dela, D-157)."""
    step = _next(task, config)
    step["chat"] = (task.get("chat") or {}).get("title")
    return step


def _next(task: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    level = effective_level(task, config)
    status = task.get("status")
    if status == STATUS_IN_DEVELOPMENT:
        returned = (task.get("queue") or {}).get("returnReason")
        if returned:
            return _stop(f"devolvida pelo executor: {returned} - corrija e rode o ship", level, "agente")
        return _step(STEP_READY, "implementar e dar o ready", level, "agente")
    if status in _AWAITING:
        mode = (config.get("delivery") or {}).get("mode") or DELIVERY_MODE_DIRECT
        return _after_ready(task, level, mode)
    if status == STATUS_IN_PR:
        return _in_pr(task, level)
    if status == STATUS_IN_QUEUE:
        return _in_queue(task, level, config)
    if status == STATUS_INTEGRATED:
        return _integrated(task, level)
    return _step(STEP_DONE, f"status {status}: nada a conduzir", level)


_HOW = {
    STEP_READY: "implemente e rode `guia ready {id} --file ... --request-test ...`",
    STEP_SHIP: "commite e rode `guia ship {id} --subject ... --body ...`",
    STEP_AUDIT: "rode `guia audit {id}`, audite com a skill anunciada e registre com `--report ... --approve`",
    STEP_QUEUE_ADD: "rode `guia queue add {id}`",
}


def announce_next(task: dict[str, Any], config: dict[str, Any]) -> None:
    """D-176: toda etapa termina dizendo o proximo passo do condutor.

    O agente que chama o motor direto (sem o texto da skill ready) nao fica
    sem trilho: a saida de ready/ship/audit/queue add ja traz o `next`.
    """
    step = next_step(task, config)
    how = _HOW.get(step["step"])
    if how:
        print(f"PROXIMO PASSO: {step['step']} - {step['why']}: {how.format(id=task['id'])}. "
              f"Siga sem perguntar: o nivel {step['level']} ja autoriza "
              "(nunca `gh pr merge` nem `queue run`).")
    elif step["step"] == STEP_STOP:
        owner = f" (destrava: {step['owner']})" if step["owner"] else ""
        print(f"PROXIMO PASSO: pare - {step['why']}{owner}.")


__all__ = ["announce_next", "next_step"]
