"""CLI handlers: depends add / remove / list (D-067).

Edita o campo `dependsOn` de uma task pos-criacao e visualiza a cadeia
com o status atual de cada dep. Determinista; nunca toca outras tasks
alem da editada.
"""

from __future__ import annotations

import argparse
import json
import sys

from _clock import today
from _constants import STATUSES_SATISFY_DEPENDENCY
from _tasks import (
    dependency_creates_cycle,
    find_task,
    find_task_or_current,
    save_task,
)


def cmd_depends_add(args: argparse.Namespace) -> int:
    """Adiciona `--on D-XYZ` (repetivel) ao `dependsOn` da task. Recusa
    auto-dependencia, dep para id inexistente (pode ser uma demanda futura
    valida, mas marcamos como erro explicito para evitar typo silencioso),
    e qualquer dep que crie ciclo.
    """
    task = find_task_or_current(args.task_id)
    existing: list[str] = list(task.get("dependsOn", []))
    seen = set(existing)
    added: list[str] = []
    for dep_id in args.on:
        if dep_id == task["id"]:
            raise SystemExit(f"Recusado: {task['id']} nao pode depender de si mesmo.")
        if find_task(dep_id) is None:
            raise SystemExit(
                f"Recusado: dependencia {dep_id} nao existe em tasks.json. "
                "Crie a demanda primeiro ou corrija o id."
            )
        if dep_id in seen:
            continue
        if dependency_creates_cycle(task["id"], dep_id):
            raise SystemExit(
                f"Recusado: declarar {task['id']} depende de {dep_id} cria ciclo "
                f"no grafo de dependencias."
            )
        existing.append(dep_id)
        seen.add(dep_id)
        added.append(dep_id)
    if added:
        task["dependsOn"] = existing
        task["updatedAt"] = today()
        save_task(task)
        print(f"{task['id']} agora depende de: {', '.join(added)}")
    else:
        print(f"{task['id']}: nada a adicionar (dependencias ja declaradas).")
    return 0


def cmd_depends_remove(args: argparse.Namespace) -> int:
    """Remove `--on D-XYZ` (repetivel) do `dependsOn`. Silencioso para
    ids que nao estavam na lista (idempotente)."""
    task = find_task_or_current(args.task_id)
    existing: list[str] = list(task.get("dependsOn", []))
    if not existing:
        print(f"{task['id']}: nenhuma dependencia declarada.")
        return 0
    targets = set(args.on)
    remaining = [dep for dep in existing if dep not in targets]
    removed = [dep for dep in existing if dep in targets]
    if not removed:
        print(f"{task['id']}: nada a remover (ids passados nao estavam declarados).")
        return 0
    if remaining:
        task["dependsOn"] = remaining
    else:
        task.pop("dependsOn", None)
    task["updatedAt"] = today()
    save_task(task)
    print(f"{task['id']}: removidas dependencias {', '.join(removed)}.")
    return 0


def cmd_depends_list(args: argparse.Namespace) -> int:
    """Lista as dependencias da task com o status atual de cada uma,
    indicando quais ainda BLOQUEIAM. Sem json: formato legivel."""
    task = find_task_or_current(args.task_id)
    deps = list(task.get("dependsOn", []))

    if args.json:
        payload = {
            "taskId": task["id"],
            "dependsOn": [
                _dep_payload(dep_id) for dep_id in deps
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if not deps:
        print(f"{task['id']}: nenhuma dependencia declarada.")
        return 0

    print(f"Dependencias de {task['id']}:")
    blocking = 0
    for dep_id in deps:
        dep_task = find_task(dep_id)
        if dep_task is None:
            print(f"  ! {dep_id} [missing] - BLOQUEIA")
            blocking += 1
            continue
        status = dep_task.get("status", "?")
        if status in STATUSES_SATISFY_DEPENDENCY:
            mark = "OK"
        else:
            mark = "BLOQUEIA"
            blocking += 1
        print(f"  - {dep_id} [{status}] {mark} - {dep_task.get('title', '')}")
    if blocking:
        print(
            f"\n{blocking} dependencia(s) bloqueando. "
            f"start/promote de {task['id']} sera recusado ate cada uma chegar a "
            "Validada/Finalizada/Resolvida/Cancelada.",
            file=sys.stderr if args.json else sys.stdout,
        )
    return 0


def _dep_payload(dep_id: str) -> dict:
    dep_task = find_task(dep_id)
    if dep_task is None:
        return {"id": dep_id, "found": False, "blocking": True}
    status = dep_task.get("status")
    return {
        "id": dep_id,
        "found": True,
        "status": status,
        "title": dep_task.get("title", ""),
        "blocking": status not in STATUSES_SATISFY_DEPENDENCY,
    }


__all__ = [
    "cmd_depends_add",
    "cmd_depends_remove",
    "cmd_depends_list",
]
