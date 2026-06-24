"""D-095 quality hook: force a consultative quality review at `finish`.

Onda 2, liberado pos-D-080. O dono quer que o `finish` SEMPRE rode uma
validacao de qualidade do que foi feito antes de fechar - nao so os comandos
de teste (esses continuam no `_validation_runner`). Esta camada estende o
conceito para acionar **SKILLS consultivas** sobre o que mudou (`modifiedFiles`),
avaliando: (a) qualidade do codigo; (b) tamanho de funcoes/arquivos;
(c) responsabilidade unica (SRP); (d) cobertura/tests; (e) se precisa refatorar.

Contrato (mesma forma do docs-hook e do gate humano D-080):
    Skills sao acionadas pelo AGENTE, nao pelo Python. Entao o core nao "roda"
    as skills - ele SINALIZA e EXIGE. O `cmd_finish` recusa o fechamento ate o
    agente confirmar que rodou a validacao consultiva (--quality-checked e/ou
    --quality-skill <nome>) OU declarar um skip explicito (--quality-skip
    "<motivo>"). A skill `guia:finish` instrui o agente a rodar as skills de
    qualidade sobre modifiedFiles antes de chamar o CLI.

Distinto de:
    D-088 - avalia DDD/SOLID ao criar LOCK (mesmo espirito, momento diferente).
    D-085 - skill valida-pasta (nota 0-10). Referenciada como skill candidata,
            nao reimplementada aqui.
"""

from __future__ import annotations

import argparse
from typing import Any

from _clock import today
from _constants import (
    GUIA_DIR,
    MSG_NONE_PLACEHOLDER,
    QUALITY_DIMENSIONS,
    QUALITY_SKILL_SUGGESTIONS,
    ROOT,
)

_GUIA_PREFIX = (GUIA_DIR.relative_to(ROOT).as_posix() + "/")


def quality_gate_enabled(config: dict[str, Any]) -> bool:
    """Liga/desliga o gate via .guia/process.json (finish.qualityGateByDefault).

    Default True: o dono quer que o finish SEMPRE valide qualidade. Projetos
    podem desligar por config; um run pode pular com --quality-skip.
    """
    return bool(config.get("finish", {}).get("qualityGateByDefault", True))


def compute_quality_candidates(
    task: dict[str, Any],
    changed_files: list[str],
) -> list[str]:
    """Arquivos do PRODUTO que mudaram e merecem avaliacao de qualidade.

    Une modifiedFiles + changed_files, descartando placeholders e a propria
    escrituracao do Guia (`.guia/**`): o catalogo/estado nao e "codigo que
    mudou", entao nao dispara o gate sozinho.
    """
    files = list(dict.fromkeys(list(task.get("modifiedFiles", [])) + (changed_files or [])))
    out: list[str] = []
    for f in files:
        if not f or f == MSG_NONE_PLACEHOLDER:
            continue
        if f.startswith(_GUIA_PREFIX):
            continue
        out.append(f)
    return out


def ensure_quality_review_ok(
    task: dict[str, Any],
    changed_files: list[str],
    config: dict[str, Any],
    args: argparse.Namespace,
) -> None:
    """Barra o finish ate o agente validar qualidade ou pular explicitamente.

    No-op quando o gate esta desligado ou nao ha arquivo de produto mudado.
    Caminho de skip explicito: --quality-skip "<motivo>".
    """
    if not quality_gate_enabled(config):
        return
    candidates = compute_quality_candidates(task, changed_files)
    if not candidates:
        return
    skipped = (getattr(args, "quality_skip", "") or "").strip()
    skills = [s for s in (getattr(args, "quality_skill", []) or []) if s]
    checked = bool(getattr(args, "quality_checked", False))
    if skipped or checked or skills:
        return
    print_quality_block(task, candidates)
    raise SystemExit(
        "quality-check: rode as skills de qualidade sobre os arquivos acima "
        "(qualidade de codigo, tamanho de funcao/arquivo, SRP, cobertura, "
        "necessidade de refatorar) e re-rode com --quality-checked "
        "(opcional: --quality-skill <nome> e/ou --quality-finding \"<acao>\"). "
        "Se nao houver nada a avaliar, use --quality-skip \"<motivo>\"."
    )


def build_quality_review_record(
    task: dict[str, Any],
    changed_files: list[str],
    args: argparse.Namespace,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "candidates": compute_quality_candidates(task, changed_files),
        "dimensions": list(QUALITY_DIMENSIONS),
        "skills": [s for s in (getattr(args, "quality_skill", []) or []) if s],
        "findings": [f for f in (getattr(args, "quality_finding", []) or []) if f],
        "checkedAt": today(),
    }
    skip = (getattr(args, "quality_skip", "") or "").strip()
    if skip:
        record["skipped"] = skip
    return record


def print_quality_block(task: dict[str, Any], candidates: list[str]) -> None:
    print()
    print(f"=== quality-check: {task.get('id')} ===")
    print(
        "Antes de fechar, rode uma validacao de qualidade do que foi feito "
        "acionando as skills de qualidade disponiveis (do PROJETO e GLOBAIS) "
        "sobre os arquivos abaixo. Avalie cada dimensao, refatore quando "
        "precisar para ficar com boa qualidade, e so entao feche."
    )
    print()
    print("Arquivos a avaliar (modifiedFiles):")
    for f in candidates:
        print(f"  - {f}")
    print()
    print("Dimensoes a checar:")
    for dim in QUALITY_DIMENSIONS:
        print(f"  - {dim}")
    print()
    print("Skills candidatas (use as que existirem no ambiente):")
    for skill in QUALITY_SKILL_SUGGESTIONS:
        print(f"  - {skill}")
    print()
    print("Como prosseguir:")
    print("  - Rodou e (se preciso) refatorou? Re-rode com --quality-checked")
    print("    [--quality-skill <nome>] [--quality-finding \"<acao tomada>\"].")
    print("  - Nada a avaliar? Re-rode com --quality-skip \"<motivo curto>\".")


__all__ = [
    "quality_gate_enabled",
    "compute_quality_candidates",
    "ensure_quality_review_ok",
    "build_quality_review_record",
    "print_quality_block",
]
