"""Skills por etapa do ciclo (D-114, R12 da especificacao de entrega por PR).

Cada etapa diz qual skill aciona. `skills.<etapa>` no process.json:

    ausente     -> o padrao do plugin para a etapa
    "nome"      -> essa skill
    ["a", "b"]  -> as duas, nessa ordem
    null        -> etapa sem skill (registrada como `disabled`)

O motor e Python e nao enxerga a lista de skills da sessao: ele ANUNCIA a
skill da etapa, o agente confere se ela existe e roda, e o motor REGISTRA o
resultado em `task["skillsRun"]` (`ran`, `missing`, `disabled`). Skill
ausente nao trava a etapa - fica visivel no registro.
"""

from __future__ import annotations

import sys
from typing import Any

from _clock import now_iso
from _constants import QUALITY_SKILL_SUGGESTIONS

STAGE_COMMIT = "commit"
STAGE_READY = "ready"
STAGE_QUALITY = "quality"

# Padroes que reproduzem o que o Guia ja sugeria. `commit` sem skill fixa:
# vale a deteccao por nome do D-054 (skill com `commit` + `conventional` ou
# `gitmoji`), descrita no corpo do ready.
SKILL_STAGE_DEFAULTS: dict[str, tuple[str, ...]] = {
    STAGE_COMMIT: (),
    STAGE_READY: ("delivery-report",),
    STAGE_QUALITY: tuple(QUALITY_SKILL_SUGGESTIONS),
}
COMMIT_AUTODETECT_HINT = "deteccao por nome (D-054: `commit` + `conventional`/`gitmoji`)"

RESULT_RAN = "ran"
RESULT_MISSING = "missing"
RESULT_DISABLED = "disabled"


def stage_skills(stage: str, config: dict[str, Any]) -> tuple[list[str], bool]:
    """(skills, desligada) da etapa segundo `config["skills"]`."""
    configured = config.get("skills") or {}
    if stage not in configured:
        return list(SKILL_STAGE_DEFAULTS.get(stage, ())), False
    value = configured[stage]
    if value is None:
        return [], True
    if isinstance(value, str):
        return ([value] if value.strip() else []), False
    return [str(item) for item in value if str(item).strip()], False


def announce_stage(stage: str, config: dict[str, Any]) -> None:
    """Diz ao agente qual skill a etapa aciona (stderr: nao suja o stdout)."""
    skills, disabled = stage_skills(stage, config)
    if disabled:
        print(f"Guia Fluxo: etapa {stage} sem skill (desligada em skills.{stage}).", file=sys.stderr)
    elif skills:
        print(
            f"Guia Fluxo: etapa {stage} -> acione {', '.join(skills)} "
            f"(se nao existir na sessao, siga e registre com --skill-missing).",
            file=sys.stderr,
        )
    elif stage == STAGE_COMMIT:
        print(f"Guia Fluxo: etapa commit -> {COMMIT_AUTODETECT_HINT}.", file=sys.stderr)


def record_stage(
    task: dict[str, Any],
    stage: str,
    config: dict[str, Any],
    ran: list[str] | None = None,
    missing: list[str] | None = None,
) -> None:
    """Acrescenta o resultado da etapa em `task["skillsRun"]`."""
    entries = task.setdefault("skillsRun", [])
    at = now_iso()
    _, disabled = stage_skills(stage, config)
    if disabled:
        entries.append({"stage": stage, "skill": None, "result": RESULT_DISABLED, "at": at})
        return
    for skill in ran or []:
        entries.append({"stage": stage, "skill": skill, "result": RESULT_RAN, "at": at})
    for skill in missing or []:
        entries.append({"stage": stage, "skill": skill, "result": RESULT_MISSING, "at": at})


__all__ = [
    "SKILL_STAGE_DEFAULTS",
    "STAGE_COMMIT",
    "STAGE_QUALITY",
    "STAGE_READY",
    "announce_stage",
    "record_stage",
    "stage_skills",
]
