"""O configurador da entrega (D-143, epico E-008).

Cada etapa e um dado: o que se decide, por que importa, o que o Guia viu no
projeto, as opcoes com a recomendada e o porque, e a chave do process.json.
O motor monta o plano e grava; quem conversa e um painel - o terminal
(D-144) ou o agente no chat (D-145) - sobre o mesmo plano, para a explicacao
morar num lugar so.

Serve de atualizador: rodado de novo, cada etapa vem com o valor atual e o
status (`nova`: falta decidir; `padrao`: ausente, mas o padrao do motor ja e o
recomendado; `ok`: igual a recomendacao; `difere`: escolha diferente). Grava o
process.json (local), com backup; o que muda o GitHub fica em notas para o dono
aplicar. A excecao e o perfil de travas (D-161, decisao do Paulo): a etapa
`locks-profile` grava o registry pelos ganchos `read`/`write` da Step.
"""

from __future__ import annotations

import copy
import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from _auto_finish import AUTO_FINISH_DEFAULT
from _autonomy import LEVELS, rank
from _constants import (
    COMMIT_FORMAT_GITMOJI,
    COMMIT_FORMAT_LEGACY,
    DELIVERY_BASE_BRANCH_DEFAULT,
    DELIVERY_MODE_DIRECT,
    DELIVERY_MODE_PR,
    GUIA_DIR,
    PROCESS_FILE,
    ROOT,
)
from _lock_profiles import PROFILE_CUSTOM, detect_profile, write_profile
from _paths import plugin_templates_dir
from _profiles import PROFILE_SOLO_DIRECT, propose_profile
from _skills import SKILL_STAGE_DEFAULTS, STAGE_AUDIT, STAGE_DEPS, STAGE_QUALITY, STAGE_READY
from _state import write_json

BACKUP_DIR = GUIA_DIR / "backups"
KEEP_DEFAULT = "padrao"  # remove a chave: vale o padrao do motor
NONE_TOKENS = ("nenhum", "nenhuma")
STATUS_NEW, STATUS_DEFAULT, STATUS_OK, STATUS_DIFFERS = "nova", "padrao", "ok", "difere"
LEVEL_LABELS = {
    "manual": "implementa e da ready",
    "pr": "+ abre o PR e audita",
    "queue": "+ enfileira ja aprovado",
    "pilot": "+ fecha a demanda quando e seguro",
}
REGISTRY_REL = ".guia/locks/registry.yaml"
GATE_SCRIPT = "bin/portao.ps1"
HEAVY_DIRS = (".venv", "venv", "node_modules")


@dataclass(frozen=True)
class Option:
    value: Any
    label: str
    why: str


@dataclass
class Context:
    facts: list[dict[str, Any]]
    config: dict[str, Any]
    root: Path

    def fact(self, name: str) -> Any:
        return next((f.get("value") for f in self.facts if f["name"] == name), None)

    def get(self, path: tuple[str, ...]) -> Any:
        return get_path(self.config, path)

    @property
    def mode(self) -> str:
        return self.get(("delivery", "mode")) or DELIVERY_MODE_DIRECT


@dataclass(frozen=True)
class Step:
    id: str
    section: str
    title: str
    explain: str
    path: tuple[str, ...]
    kind: str  # choice | text | list
    default: Any
    recommend: Callable[[Context], tuple[Any, str]]
    options: Callable[[Context], list[Option]] = lambda ctx: []
    seen: Callable[[Context], list[str]] = lambda ctx: []
    applies: Callable[[Context], bool] = lambda ctx: True
    note: str | None = None
    # D-161: valor que mora fora do process.json (ex.: o registry de travas).
    # `read` da o valor atual; `write` grava o escolhido e devolve o backup.
    read: Callable[[Context], Any] | None = None
    write: Callable[[Any], Path | None] | None = None


# --- caminhos no process.json ------------------------------------------------


def get_path(config: dict[str, Any], path: tuple[str, ...]) -> Any:
    node: Any = config
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def _set_path(config: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    node = config
    for key in path[:-1]:
        node = node.setdefault(key, {})
    node[path[-1]] = value


def _del_path(config: dict[str, Any], path: tuple[str, ...]) -> None:
    parent = get_path(config, path[:-1]) if len(path) > 1 else config
    if isinstance(parent, dict):
        parent.pop(path[-1], None)


# --- deteccao no projeto ----------------------------------------------------


def _gate_candidates(root: Path) -> tuple[list[str], str]:
    if (root / GATE_SCRIPT).is_file():
        return [f"powershell -NoProfile -ExecutionPolicy Bypass -File {GATE_SCRIPT}"], f"achei {GATE_SCRIPT}"
    if (root / "pyproject.toml").is_file() or (root / "tests").is_dir():
        return ["python -m pytest -q"], "projeto Python na raiz (pyproject.toml ou tests/)"
    if "test" in _package_scripts(root / "package.json"):
        return ["npm test"], "package.json na raiz com o script test"
    return [], f"nenhum portao de um comando so na raiz (sugestao: um {GATE_SCRIPT} que rode tudo)"


def _package_scripts(path: Path) -> dict[str, Any]:
    """Scripts do package.json; malformado ou ausente, nenhum (so pula a sugestao)."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    scripts = data.get("scripts") if isinstance(data, dict) else None
    return scripts if isinstance(scripts, dict) else {}


def _heavy_dirs(root: Path) -> list[str]:
    """Pastas pesadas e locais (.venv, node_modules) na raiz e um nivel abaixo."""
    found = [name for name in HEAVY_DIRS if (root / name).is_dir()]
    for child in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")):
        found += [f"{child.name}/{name}" for name in HEAVY_DIRS if (child / name).is_dir()]
    return found


def _lock_ids() -> list[str]:
    try:
        import _locks

        return [str(lock.get("id")) for lock in _locks.lock_api.load_locks() if lock.get("id")]
    except Exception:  # registro ausente ou invalido: a etapa so nao lista
        return []


# --- as etapas --------------------------------------------------------------


def _is_pr(ctx: Context) -> bool:
    return ctx.mode == DELIVERY_MODE_PR


def _recommend_mode(ctx: Context) -> tuple[Any, str]:
    profile, reasons = propose_profile(ctx.facts)
    value = DELIVERY_MODE_DIRECT if profile == PROFILE_SOLO_DIRECT else DELIVERY_MODE_PR
    return value, f"perfil {profile}: " + "; ".join(reasons)


def _seen_mode(ctx: Context) -> list[str]:
    protection = ctx.fact("protection") or {}
    audit = ctx.fact("audit-workflow") or {}
    return [
        f"remoto: {ctx.fact('remote') or 'nenhum'}",
        f"checks exigidos na base: {', '.join(protection.get('checks') or []) or 'nenhum'}",
        f"workflow de auditoria: {audit.get('file') or 'nenhum'}",
    ]


def _recommend_audit(ctx: Context) -> tuple[Any, str]:
    audit = ctx.fact("audit-workflow") or {}
    if audit.get("statusContext"):
        return audit["statusContext"], f"e o status que {audit['file']} grava"
    return ctx.get(("delivery", "audit", "statusContext")), "sem workflow de auditoria: `guia scaffold auditoria` gera um"


def _recommend_changelog(ctx: Context) -> tuple[Any, str]:
    if _is_pr(ctx):
        return "fragments", "com varios PRs na fila, todos editando o [Unreleased] conflitam a cada merge"
    return "inline", "no modo direct um commit por vez nao disputa a mesma linha"


def _describe_changelog(fact: dict[str, Any] | None) -> str:
    if not fact:
        return "sem CHANGELOG.md"
    parts = ["CHANGELOG.md com [Unreleased]" if fact.get("unreleased") else "CHANGELOG.md sem [Unreleased]"]
    if fact.get("fragmentsDir"):
        parts.append(f"fragmentos em {fact['fragmentsDir']}/")
    return ", ".join(parts)


def _recommend_gate(ctx: Context) -> tuple[Any, str]:
    current = ctx.get(("delivery", "gate", "full"))
    if current:
        return current, "o portao ja configurado"
    commands, why = _gate_candidates(ctx.root)
    return commands, why


def _recommend_junctions(ctx: Context) -> tuple[Any, str]:
    found = _heavy_dirs(ctx.root)
    return found, ("pastas locais pesadas: o worktree as enxerga sem reinstalar" if found else "nenhuma pasta pesada achada")


def _recommend_locks(ctx: Context) -> tuple[Any, str]:
    return "*", "todas: desbloquear trava e sempre decisao do dono, o mais seguro para comecar"


def _lock_options(ctx: Context) -> list[Option]:
    ids = _lock_ids()
    options = [Option("*", "todas as travas", "qualquer [unlock:] para no dono")]
    if "adicoes-exigem-autorizacao" in ids:
        others = [lock for lock in ids if lock != "adicoes-exigem-autorizacao"]
        label = f"so {', '.join(others)}" if others else "nenhuma (so os caminhos sensiveis param)"
        options.append(Option(others, label + " - sem adicoes-exigem-autorizacao",
                              "quase todo PR traz arquivo novo; com ela, quase todo PR espera o approve"))
    return options


LOCK_PROFILE_OPTIONS = (
    Option("adicoes", "todo arquivo novo pede [unlock:]", "o agente nao cria arquivo sem voce saber"),
    Option("testes", "teste existente vira contrato; arquivo novo livre", "o comportamento garantido nao muda escondido"),
    Option("nenhum", "nada travado; o hook fica instalado", "trave depois so o que for homologado"),
)


def _registry() -> Path:
    import _locks  # tardio, como _lock_ids: o registry e do projeto, nao do plugin

    return _locks.lock_api.REGISTRY


def _templates_available() -> bool:
    """Sem os templates do plugin nao ha perfil para gravar: a etapa nao se aplica."""
    templates = plugin_templates_dir()
    return templates is not None and (templates / "locks").is_dir()


def _read_lock_profile(ctx: Context) -> str | None:
    return detect_profile(_registry(), plugin_templates_dir())


def _recommend_lock_profile(ctx: Context) -> tuple[Any, str]:
    if _read_lock_profile(ctx) == PROFILE_CUSTOM:
        return PROFILE_CUSTOM, "manter: o registry tem travas proprias, que trocar de perfil apagaria"
    return "testes", "quase todo PR traz arquivo novo; travar so os testes existentes protege o comportamento sem parar cada PR"


def _write_lock_profile(profile: Any) -> Path | None:
    return write_profile(str(profile), plugin_templates_dir(), _registry(), BACKUP_DIR)


def _skills_step(stage: str, title: str, explain: str) -> Step:
    default = list(SKILL_STAGE_DEFAULTS.get(stage, ()))

    def recommend(ctx: Context) -> tuple[Any, str]:
        current = ctx.get(("skills", stage))
        return (current, "a ja configurada") if current is not None else (default, "o padrao do Guia")

    return Step(f"skills-{stage}", "Skills", title, explain, ("skills", stage), "list", default, recommend)


STEPS: tuple[Step, ...] = (
    Step(
        "mode", "Entrega", "Modo de entrega",
        "Como o codigo chega a main. `direct`: o finish commita na main, como sempre. `pr`: cada demanda vive "
        "num worktree e chega por pull request - auditoria, fila e executor so existem neste modo.",
        ("delivery", "mode"), "choice", DELIVERY_MODE_DIRECT, _recommend_mode,
        options=lambda ctx: [
            Option(DELIVERY_MODE_DIRECT, "commit direto na main", "projeto solo, sem PR nem CI exigido"),
            Option(DELIVERY_MODE_PR, "tudo por pull request", "main protegida, CI e auditoria antes do merge"),
        ],
        seen=_seen_mode,
    ),
    Step(
        "base-branch", "Entrega", "Branch base",
        "A branch que recebe os PRs: dela nascem os worktrees, contra ela se calcula o diff e o patch-id.",
        ("delivery", "baseBranch"), "text", DELIVERY_BASE_BRANCH_DEFAULT,
        lambda ctx: (ctx.get(("delivery", "baseBranch")) or DELIVERY_BASE_BRANCH_DEFAULT, "a branch principal do repositorio"),
        applies=_is_pr,
    ),
    Step(
        "commit-format", "Commit", "Formato do commit",
        "`gitmoji-conventional`: `<emoji> <tipo>(D-NNN): titulo`, o porque no corpo e as marcas [unlock:] "
        "calculadas pelo git. `legacy`: o formato antigo do Guia (`feature(D-NNN): titulo` com o resumo).",
        ("delivery", "commit", "format"), "choice", COMMIT_FORMAT_LEGACY,
        lambda ctx: (COMMIT_FORMAT_GITMOJI, "o formato do modo pr (titulo do PR = assunto do commit)")
        if _is_pr(ctx) else (ctx.get(("delivery", "commit", "format")) or COMMIT_FORMAT_LEGACY, "o que ja vale"),
        options=lambda ctx: [
            Option(COMMIT_FORMAT_GITMOJI, "`<emoji> <tipo>(D-NNN): titulo`", "padrao dos projetos por PR"),
            Option(COMMIT_FORMAT_LEGACY, "`feature(D-NNN): titulo` com o resumo", "o formato historico do Guia"),
        ],
        seen=lambda ctx: [f"hooksPath: {(ctx.fact('hooks') or {}).get('hooksPath') or 'nenhum'}"],
    ),
    Step(
        "commit-coauthor", "Commit", "Coautoria do commit",
        "A linha `Co-Authored-By` no fim de cada commit montado pelo Guia. Vazio: sem a linha.",
        ("delivery", "commit", "coAuthor"), "text", None,
        lambda ctx: (ctx.get(("delivery", "commit", "coAuthor")), "a ja configurada (ou nenhuma)"),
    ),
    Step(
        "audit-status", "Auditoria", "Status da auditoria",
        "O nome do status que o workflow de auditoria grava no head do PR quando o dono comenta o marcador. "
        "O executor e o doctor conferem que a protecao exige exatamente este nome.",
        ("delivery", "audit", "statusContext"), "text", None, _recommend_audit,
        seen=lambda ctx: [f"workflow de auditoria: {(ctx.fact('audit-workflow') or {}).get('file') or 'nenhum'}"],
        applies=_is_pr,
        note="Sem o workflow, `guia scaffold auditoria` o gera; a protecao precisa exigir o status (`guia scaffold protection`).",
    ),
    Step(
        "changelog-style", "Changelog", "Estilo do CHANGELOG",
        "`inline`: cada demanda escreve no [Unreleased] do CHANGELOG.md. `fragments`: cada demanda grava o "
        "proprio changelog.d/<ID>.<categoria>.md e a release junta tudo (`guia changelog compile`).",
        ("delivery", "changelog", "style"), "choice", "inline", _recommend_changelog,
        options=lambda ctx: [
            Option("fragments", "um arquivo por demanda", "sem conflito entre PRs na fila"),
            Option("inline", "direto no CHANGELOG.md", "simples, para quem entrega um por vez"),
        ],
        seen=lambda ctx: [_describe_changelog(ctx.fact("changelog")),
                          f"scripts de release: {', '.join((ctx.fact('release') or {}).get('scripts') or []) or 'nenhum'}"],
        note="Com fragments e um script de release proprio, o script precisa compilar os fragmentos (docs/propostas/release-py-fragmentos.md).",
    ),
    Step(
        "gate", "Portao", "Portao do ship",
        "Os comandos que o `ship` roda no worktree antes de abrir o PR; um falhou, nada e enviado. Cada "
        "comando roda na raiz do worktree - para portao em varias pastas, um script que rode tudo.",
        ("delivery", "gate", "full"), "list", [], _recommend_gate,
        seen=lambda ctx: [_gate_candidates(ctx.root)[1]],
        applies=_is_pr,
    ),
    Step(
        "queue-conflicts", "Fila", "O que a fila faz com conflito",
        "Quando um PR conflita com a main (ou muda depois da auditoria). `manager`: ele fica na fila e o gerente "
        "(o chat que roda `/guia:queue-control run`) resolve - rebase preservando as duas intencoes, portao, auditoria "
        "do delta, de volta a fila - e so o que pede decisao chega ao dono. `return`: volta ao autor, que resolve no chat dele.",
        ("delivery", "queue", "conflicts"), "choice", "return",
        lambda ctx: ("manager", "conflito e o trabalho que a fila existe para fazer; voce so ve o que pede decisao")
        if _is_pr(ctx) else ("return", "sem fila no modo direct"),
        options=lambda ctx: [
            Option("manager", "o gerente da fila resolve", "a fila segue sozinha; decisao vai ao dono com o chat"),
            Option("return", "volta ao autor", "cada chat resolve o proprio conflito"),
        ],
        applies=_is_pr,
    ),
    Step(
        "worktree-junctions", "Worktree", "Juncoes do worktree",
        "Pastas da arvore principal que o worktree da demanda enxerga por juncao, sem reinstalar "
        "(ex.: backend/.venv, frontend/node_modules). Removidas com seguranca no fim.",
        ("delivery", "worktree", "junctions"), "list", [], _recommend_junctions,
        seen=lambda ctx: [f"pastas pesadas: {', '.join(_heavy_dirs(ctx.root)) or 'nenhuma'}"],
        applies=_is_pr,
    ),
    Step(
        "worktree-env", "Worktree", "Arquivos de ambiente copiados",
        "Arquivos copiados da arvore principal para cada worktree (ex.: .env). Cuidado: segredo copiado "
        "e segredo espalhado; prefira deixar vazio e criar o necessario por worktree.",
        ("delivery", "worktree", "envFiles"), "list", [],
        lambda ctx: (ctx.get(("delivery", "worktree", "envFiles")) or [], "vazio: nenhum segredo espalhado"),
        applies=_is_pr,
    ),
    _skills_step(STAGE_READY, "Skill do relatorio de entrega",
                 "A skill que o agente roda no `ready` para o relatorio (o que foi feito, como validar, o que falta)."),
    _skills_step(STAGE_QUALITY, "Skills de qualidade",
                 "As skills que revisam o codigo antes de fechar. A que nao existir na sessao e pulada e registrada."),
    _skills_step(STAGE_AUDIT, "Skill de auditoria",
                 "A skill que audita o PR antes do merge. Sem ela, o agente usa o checklist embutido do Guia - "
                 "a auditoria nunca vira aprovacao por falta de skill."),
    _skills_step(STAGE_DEPS, "Skill das dependencias",
                 "A skill que resolve o lote do Dependabot no `/guia:deps --now`: junta as versoes, aplica o piso "
                 "de supply-chain e roda o portao uma vez. Sem ela o lote para e avisa - juntar versoes exige juizo."),
    Step(
        "autonomy-default", "Autonomia", "Nivel padrao de autonomia",
        "Ate onde o agente vai sozinho em cada demanda. manual: implementa e da ready. pr: + abre o PR e "
        "audita. queue: + enfileira ja aprovado. pilot: + fecha a demanda quando todas as condicoes provam "
        "que e seguro. Cada demanda pode ter o seu (`/guia:autonomy`).",
        ("autonomy", "default"), "choice", "manual",
        lambda ctx: ("pr", "o agente lanca o PR, mas todo merge espera o seu approve") if _is_pr(ctx)
        else ("manual", "no modo direct nao ha PR nem fila"),
        options=lambda ctx: [Option(level, LEVEL_LABELS[level], "") for level in LEVELS],
    ),
    Step(
        "autonomy-ceiling", "Autonomia", "Teto de autonomia do projeto",
        "O nivel maximo que qualquer demanda pode ter neste projeto; pedido acima e recusado.",
        ("autonomy", "ceiling"), "choice", "pilot",
        lambda ctx: ("queue", "a fila aprova sozinha o que e seguro; fechar sozinho (pilot) fica para depois de medir"),
        options=lambda ctx: [Option(level, LEVEL_LABELS[level], "") for level in LEVELS],
    ),
    Step(
        "deps-autonomy", "Autonomia", "Nivel do lote de dependencias",
        "Ate onde o `/guia:deps --now` vai sozinho com o lote do Dependabot. pr: lanca o PR e audita. queue: + "
        "entra na fila. pilot: + integra e fecha, e so pergunta quando ha algo alem de versao (codigo, linha de "
        "base, trava) ou a skill achar uma decisao. Limitado pelo teto do projeto. Padrao: o nivel padrao.",
        ("delivery", "dependencies", "autonomy"), "choice", None,
        lambda ctx: (ctx.get(("delivery", "dependencies", "autonomy")), "o ja configurado (ou o nivel padrao)")
        if ctx.get(("delivery", "dependencies", "autonomy")) else (None, "segue o nivel padrao ate voce decidir"),
        options=lambda ctx: [Option(level, LEVEL_LABELS[level], "") for level in LEVELS],
        applies=_is_pr,
    ),
    Step(
        "auto-finish-kinds", "Autonomia", "Que tipos a fila fecha sozinha",
        "No pilot, depois do merge a fila fecha a demanda quando todas as condicoes provam que e seguro (main verde, "
        "auditoria sem achados, sem tela, nada sensivel; bug com teste). Esta etapa escolhe os tipos. O padrao deixa "
        "`feature` de fora: capacidade nova pede uso real antes do 'esta bom' - fica Integrada esperando o seu finish.",
        ("autonomy", "autoFinish", "kinds"), "list", list(AUTO_FINISH_DEFAULT["kinds"]),
        lambda ctx: (ctx.get(("autonomy", "autoFinish", "kinds")) or list(AUTO_FINISH_DEFAULT["kinds"]),
                     "o ja configurado" if ctx.get(("autonomy", "autoFinish", "kinds")) else "o padrao do Guia (sem feature)"),
        options=lambda ctx: [
            Option(list(AUTO_FINISH_DEFAULT["kinds"]), "chore, test, docs, refactor, bug", "feature espera o seu finish"),
            Option([*AUTO_FINISH_DEFAULT["kinds"], "feature"], "todos, inclusive feature",
                   "a fila fecha tudo que as condicoes provarem; voce so entra quando algo nao se prova"),
        ],
        applies=lambda ctx: (ctx.get(("autonomy", "ceiling")) or "pilot") == "pilot",
    ),
    Step(
        "locks-profile", "Travas", "Perfil de travas",
        "Quais arquivos pedem [unlock:] no commit. adicoes: todo arquivo novo. testes: alterar, apagar ou "
        "renomear um teste existente; arquivo novo fica livre. nenhum: nada travado. Gravar TROCA o "
        ".guia/locks/registry.yaml pelo template do perfil - o anterior vai para .guia/backups/.",
        (REGISTRY_REL,), "choice", None, _recommend_lock_profile,
        options=lambda ctx: list(LOCK_PROFILE_OPTIONS),
        seen=lambda ctx: [f"travas do projeto: {', '.join(_lock_ids()) or 'nenhuma'}"],
        applies=lambda ctx: _templates_available(),
        read=_read_lock_profile,
        write=_write_lock_profile,
        note="Unica etapa que grava fora do process.json (D-161). `personalizado`: travas proprias, mantidas.",
    ),
    Step(
        "always-human-locks", "Autonomia", "Travas que sempre param no dono",
        "No nivel queue ou acima, PR que desbloqueia uma destas travas ([unlock:]) espera o seu approve, "
        "mesmo aprovado pela autonomia. Caminhos sensiveis (.github/**, migrations, lockfiles) sempre param.",
        ("autonomy", "alwaysHumanLocks"), "list", "*", _recommend_locks,
        options=_lock_options,
        seen=lambda ctx: [f"travas do projeto: {', '.join(_lock_ids()) or 'nenhuma'}"],
        applies=lambda ctx: rank(ctx.get(("autonomy", "ceiling")) or "pilot") >= rank("queue"),
    ),
)
STEPS_BY_ID = {step.id: step for step in STEPS}


# --- plano, valores e gravacao ----------------------------------------------


def parse_value(step: Step, raw: str) -> Any:
    """Texto do usuario -> valor da chave (KEEP_DEFAULT remove a chave)."""
    text = raw.strip()
    if text.lower() == KEEP_DEFAULT:
        return KEEP_DEFAULT
    if step.kind == "choice":
        values = [str(option.value) for option in step.options(Context([], {}, Path(".")))] or [str(step.default)]
        if text not in values:
            raise SystemExit(f"{step.id}: {text!r} nao e uma opcao ({', '.join(values)}).")
        return text
    if step.kind == "text":
        return KEEP_DEFAULT if not text or text.lower() in NONE_TOKENS else text
    if text.lower() in NONE_TOKENS:
        return []
    if text == "*":
        return "*"
    if text.startswith("["):
        value = json.loads(text)
        if not isinstance(value, list):
            raise SystemExit(f"{step.id}: esperava uma lista JSON.")
        return [str(item) for item in value]
    return [item.strip() for item in text.split(",") if item.strip()]


def apply_answers(config: dict[str, Any], answers: dict[str, str]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Config nova (copia) e a lista de mudancas `{step, path, before, after}`."""
    updated = copy.deepcopy(config)
    changes = []
    for step_id, raw in answers.items():
        step = STEPS_BY_ID.get(step_id)
        if step is None:
            raise SystemExit(f"Etapa desconhecida {step_id!r}: use uma de {', '.join(STEPS_BY_ID)}.")
        value = parse_value(step, raw)
        if step.write:
            # D-161: fora do process.json - a config nao muda; o save grava pelo `write`.
            before = step.read(Context([], updated, ROOT)) if step.read else None
            after = before if value == KEEP_DEFAULT else value
            if before != after:
                changes.append({"step": step_id, "path": ".".join(step.path), "before": before, "after": after,
                                "external": True})
            continue
        before = get_path(updated, step.path)
        if value == KEEP_DEFAULT:
            _del_path(updated, step.path)
        else:
            _set_path(updated, step.path, value)
        after = get_path(updated, step.path)
        if before != after:
            changes.append({"step": step_id, "path": ".".join(step.path), "before": before, "after": after})
    return updated, changes


def _status(current: Any, default: Any, recommended: Any) -> str:
    if current is None:
        return STATUS_DEFAULT if default == recommended else STATUS_NEW
    return STATUS_OK if current == recommended else STATUS_DIFFERS


def build_plan(config: dict[str, Any], facts: list[dict[str, Any]], root: Path) -> list[dict[str, Any]]:
    """Cada etapa, na ordem, com o que precisa para ser decidida."""
    ctx = Context(facts, config, root)
    plan = []
    for step in STEPS:
        current = step.read(ctx) if step.read else ctx.get(step.path)
        recommended, why = step.recommend(ctx)
        status = _status(current, step.default, recommended)
        plan.append({
            "id": step.id, "section": step.section, "title": step.title, "explain": step.explain,
            "path": ".".join(step.path), "kind": step.kind, "default": step.default,
            "current": current, "recommended": recommended, "recommendedWhy": why, "status": status,
            "options": [{"value": o.value, "label": o.label, "why": o.why} for o in step.options(ctx)],
            "seen": step.seen(ctx), "applies": step.applies(ctx), "note": step.note,
        })
    return plan


def outside_notes(config: dict[str, Any], facts: list[dict[str, Any]]) -> list[str]:
    """O que o configurador nao grava (GitHub, scripts) e o dono aplica."""
    ctx = Context(facts, config, Path("."))
    if not _is_pr(ctx):
        return []
    notes = []
    if not (ctx.fact("protection") or {}).get("checks"):
        notes.append("A base nao exige checks: `guia scaffold protection` imprime o comando de protecao.")
    if not ctx.fact("audit-workflow"):
        notes.append("Sem workflow de auditoria: `guia scaffold auditoria` gera um.")
    scripts = (ctx.fact("release") or {}).get("scripts") or []
    if ctx.get(("delivery", "changelog", "style")) == "fragments" and scripts:
        notes.append(f"Com fragments, {', '.join(scripts)} precisa compilar os fragmentos (`guia changelog compile`).")
    return notes


def save(config: dict[str, Any], changes: list[dict[str, Any]] | None = None) -> Path | None:
    """Grava o process.json; o anterior vai para .guia/backups/ (None se nao havia).

    D-161: mudanca `external` (fora do process.json) grava pelo `write` da
    etapa, que guarda o backup em `change["backup"]`; so mudanca externa nao
    reescreve o process.json.
    """
    external = [change for change in changes or [] if change.get("external")]
    for change in external:
        written = STEPS_BY_ID[change["step"]].write(change["after"])
        change["backup"] = str(written) if written else None
    if changes is not None and len(external) == len(changes):
        return None
    backup = None
    if PROCESS_FILE.is_file():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backup = BACKUP_DIR / f"process.json.{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        shutil.copy2(PROCESS_FILE, backup)
    write_json(PROCESS_FILE, config, readable=True)
    return backup


__all__ = [
    "KEEP_DEFAULT", "STEPS", "STEPS_BY_ID", "apply_answers", "build_plan", "get_path",
    "outside_notes", "parse_value", "save",
]
