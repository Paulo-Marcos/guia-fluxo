"""Painel do terminal do configurador (D-144, epico E-008).

Uma etapa por vez, com a mesma explicacao do plano (`guia configure --plan`):
Enter aceita a recomendada, um numero escolhe a opcao, `m` mantem o atual,
`q` sai sem gravar, qualquer outro texto vira o valor. A cada resposta o plano
e recalculado - escolher `direct` faz as etapas do modo pr sumirem na hora. No
fim, o resumo `antes -> depois` e a confirmacao; nada e gravado sem `s`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from _configure import STEPS_BY_ID, apply_answers, build_plan, outside_notes, parse_value, save

KEEP, QUIT = "m", "q"
PENDING_STATUSES = ("nova", "difere")
HELP = "Enter = recomendada | numero = opcao | m = manter o atual | q = sair sem gravar | ou digite o valor"


def _raw(value: Any) -> str:
    """Valor de opcao/recomendacao -> o texto que `parse_value` entende."""
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


def _ask_step(item: dict[str, Any], ask: Callable[[str], str], say: Callable[[str], None]) -> str | None:
    """Resposta crua da etapa (None = manter); levanta KeyboardInterrupt no `q`."""
    step = STEPS_BY_ID[item["id"]]
    while True:
        answer = ask(f"  > {item['id']} [{HELP}]: ").strip()
        if answer.lower() == QUIT:
            raise KeyboardInterrupt
        if answer.lower() == KEEP:
            return None
        if not answer:
            return None if item["recommended"] is None else _raw(item["recommended"])
        if answer.isdigit() and 1 <= int(answer) <= len(item["options"]):
            return _raw(item["options"][int(answer) - 1]["value"])
        try:
            parse_value(step, answer)
        except (SystemExit, ValueError) as error:
            say(f"  {error} - tente de novo.")
            continue
        return answer


def run(config: dict[str, Any], facts: list[dict[str, Any]], root: Path, show_step: Callable[[int, dict[str, Any]], None],
        show_changes: Callable[..., None], ask: Callable[[str], str] = input, say: Callable[[str], None] = print,
        only_pending: bool = False) -> int:
    answers: dict[str, str] = {}
    say("Configurador da entrega - uma etapa por vez. " + HELP + ".")
    try:
        for index, step_id in enumerate(STEPS_BY_ID, start=1):
            current, _changes = apply_answers(config, answers)
            item = next(i for i in build_plan(current, facts, root) if i["id"] == step_id)
            if not item["applies"] or (only_pending and item["status"] not in PENDING_STATUSES):
                continue
            show_step(index, item)
            answer = _ask_step(item, ask, say)
            if answer is not None:
                answers[step_id] = answer
    except (KeyboardInterrupt, EOFError):
        say("\nSaiu sem gravar.")
        return 1
    updated, changes = apply_answers(config, answers)
    say("\nResumo:")
    show_changes(changes, outside_notes(updated, facts), False, None)
    if not changes:
        return 0
    if ask("Gravar? [s/N]: ").strip().lower() not in ("s", "sim", "y", "yes"):
        say("Nada gravado.")
        return 0
    backup = save(updated, changes)
    show_changes(changes, [], True, backup)
    return 0


__all__ = ["run"]
