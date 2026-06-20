#!/usr/bin/env python3
"""Render per-agent skill files and standalone bin/ from core/manifest/manifest.yaml.

Source of truth:
    core/manifest/manifest.yaml   (skills index: verbs + descriptions + body refs)
    core/manifest/bodies/*.md     (skill bodies - Layout B, F-016)
    core/src/*.py                 (motor + helpers - todos copiados para plugins/guia/bin/)
    core/lock/lock_api.py         (modulo de locks reutilizavel - tambem em plugins/guia/bin/)
    core/bin/guia.ps1             (wrapper PowerShell copiado para plugins/guia/bin/)
    core/templates/...            (templates copiados para plugins/guia/templates/)

Manifest schema:
    version: 2
    verbs:
      <verb>:
        description: |
          ...trigger description...
        targets:
          agent_skill:
            body_file: bodies/<verb>.agent.md    # path relativo a core/manifest/
            # ou body: |  (legacy v1, ainda aceito)
            #   ...inline markdown...
          claude_command:
            body_file: bodies/<verb>.claude.md

    Para shared body entre targets, aponte ambos para o mesmo arquivo.

Generated targets (por verbo):
    plugins/guia/commands/<verb>.md                     (Claude Code - plugin command -> /guia:<verb>)
    plugins/guia/.agents/skills/guia-<verb>/SKILL.md    (Codex + Antigravity - prefixo `guia-`)

Generated bin/ (motor standalone do plugin):
    plugins/guia/bin/guia.py      (entry point, copia exata de core/src/guia.py)
    plugins/guia/bin/_*.py        (modulos sibling: _constants, _state, _tasks, etc.)
    plugins/guia/bin/lock_api.py  (lock domain - copiado de core/lock/lock_api.py)
    plugins/guia/bin/guia.ps1     (copia de core/bin/guia.ps1 com path adaptado para layout flat)
    plugins/guia/bin/guia         (shim POSIX que chama python3 guia.py "$@")

Generated templates/:
    plugins/guia/templates/.githooks/commit-msg
    plugins/guia/templates/features/registry.yaml
    plugins/guia/templates/features/lock-ignore.txt

Hardening (F-015):
- TEMPLATE_FILES validado: --check detecta arquivos em core/templates/ nao listados.
- Renderer aborta (exit 2) se o marcador `..\\src\\guia.py` sumir do wrapper.
- YAML dos templates e validado via yaml.safe_load antes de copiar.
- dataclass Output substitui a tupla de 4 elementos.
- --check-orphans lista arquivos em plugins/guia/bin/, commands/ ou .agents/skills/ sem correspondente.
- Description vazia gera erro explicito em vez de SKILL.md silenciosamente quebrado.

Design (D-059):
- `Paths` (frozen) carrega toda config de caminho; construido uma vez e
  passado explicitamente as funcoes de coleta (sem estado global mutavel).
- Validacao/parse lancam `RenderError`; `main()` mapeia para exit 2.
  Funcoes de coleta ficam puras e testaveis sem capturar SystemExit.
- `TARGETS` (registro) concentra o conhecimento por host (nome, diretorio
  destino, sufixo de include_per_target, label) num lugar so.

Usage:
    python core/build/render-skills.py
    python core/build/render-skills.py --check
    python core/build/render-skills.py --verb feature
    python core/build/render-skills.py --check-orphans
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import Callable

try:
    import yaml
except ImportError:
    sys.stderr.write("Erro: PyYAML nao instalado. Rode: pip install pyyaml\n")
    sys.exit(2)


ROOT = Path(__file__).resolve().parents[2]


class RenderError(Exception):
    """Falha de build do renderer.

    Lancada pelas funcoes de coleta/validacao em vez de encerrar o
    processo diretamente. `main()` captura e mapeia para exit code 2,
    mantendo o nucleo de transformacao puro e testavel (D-059, P2).
    """


# --- Config / paths (D-059, P1) -------------------------------------------


@dataclass(frozen=True)
class Paths:
    """Todos os caminhos de fonte e destino do build.

    Substitui o estado global mutavel anterior: construido uma vez em
    `main()` (ou nos testes) e passado explicitamente. Imutavel; use
    `dataclasses.replace` para variacoes (sandbox de teste, --output-dir).
    """

    root: Path
    manifest_dir: Path
    manifest: Path
    bodies_dir: Path
    dist_dir: Path
    command_dir: Path
    agent_skill_dir: Path
    bin_dir: Path
    templates_dir: Path
    core_src_dir: Path
    engine_src: Path
    lock_api_src: Path
    check_lock_src: Path
    wrapper_src: Path
    templates_src: Path

    @classmethod
    def build(cls, root: Path, dist_dir: Path | None = None) -> "Paths":
        manifest_dir = root / "core" / "manifest"
        dist = (dist_dir if dist_dir is not None else root / "plugins" / "guia").resolve()
        return cls(
            root=root,
            manifest_dir=manifest_dir,
            manifest=manifest_dir / "manifest.yaml",
            bodies_dir=manifest_dir / "bodies",
            dist_dir=dist,
            command_dir=dist / "commands",
            agent_skill_dir=dist / ".agents" / "skills",
            bin_dir=dist / "bin",
            templates_dir=dist / "templates",
            core_src_dir=root / "core" / "src",
            engine_src=root / "core" / "src" / "guia.py",
            lock_api_src=root / "core" / "lock" / "lock_api.py",
            check_lock_src=root / "core" / "lock" / "check-lock.py",
            wrapper_src=root / "core" / "bin" / "guia.ps1",
            templates_src=root / "core" / "templates",
        )


# Marcador usado por core/bin/guia.ps1 para resolver o motor. No plugins/guia/, o
# layout vira flat (guia.py vizinho do wrapper), entao o marcador e
# reescrito. Aborta se ausente: o renderer presume invariante.
WRAPPER_MARKER = "..\\src\\guia.py"
WRAPPER_REPLACEMENT = "guia.py"

# Templates copiados byte-a-byte para plugins/guia/templates/. Validacao
# estrutural por extensao: arquivos .yaml passam por yaml.safe_load.
TEMPLATE_FILES: list[tuple[str, str]] = [
    ("features/registry.yaml", "features/registry.yaml"),
    ("features/lock-ignore.txt", "features/lock-ignore.txt"),
]

# Templates "promovidos" a partir de outros lugares do core/. F-018
# consolidou `core/hooks/commit-msg` como fonte unica - o renderer
# replica em `plugins/guia/templates/.githooks/commit-msg` para o instalador
# usar no consumer. Fonte como tupla relativa a paths.root.
PROMOTED_TEMPLATES: list[tuple[tuple[str, ...], str]] = [
    (("core", "hooks", "commit-msg"), ".githooks/commit-msg"),
]

POSIX_SHIM = (
    "#!/usr/bin/env bash\n"
    "# Auto-gerado por core/build/render-skills.py. Nao edite.\n"
    'exec python3 "$(dirname "$0")/guia.py" "$@"\n'
)


@dataclass(frozen=True)
class Output:
    path: Path
    target: str
    name: str
    content: str


# --- Target registry (D-059, P3) ------------------------------------------


def _agent_skill_name(verb: str) -> str:
    return verb if verb.startswith("guia-") else f"guia-{verb}"


@dataclass(frozen=True)
class TargetSpec:
    """Tudo que difere entre os hosts de skill num lugar so.

    Adicionar um host novo = adicionar uma entrada em TARGETS. As funcoes
    de render/path/host-suffix consultam o registro em vez de espalhar
    `if target == ...` (fecha OCP).
    """

    key: str
    host_suffix: str  # sufixo usado por {{include_per_target: base}} -> base.<suffix>.md
    label: str
    name_of: Callable[[str], str]
    dir_of: Callable[[Paths], Path]
    # Quando True, o alvo e um plugin *command* do Claude Code: arquivo flat
    # `<dir>/<verb>.md` sem `name:` no frontmatter (o stem do arquivo vira o
    # nome). Comandos surgem namespaced (`/guia:<verb>`); skills surgem bare.
    # Quando False (default), e um Agent Skill: `<dir>/<name>/SKILL.md` com
    # `name:` no frontmatter (convencao AGENTS.md, Codex/Antigravity).
    emits_command: bool = False

    def skill_name(self, verb: str) -> str:
        return self.name_of(verb)

    def output_path(self, verb: str, paths: Paths) -> Path:
        if self.emits_command:
            return self.dir_of(paths) / f"{self.skill_name(verb)}.md"
        return self.dir_of(paths) / self.skill_name(verb) / "SKILL.md"


TARGETS: dict[str, TargetSpec] = {
    "agent_skill": TargetSpec(
        key="agent_skill",
        host_suffix="agent",
        label="plugins/guia/.agents/skills/guia-<verb>/SKILL.md",
        name_of=_agent_skill_name,
        dir_of=lambda p: p.agent_skill_dir,
    ),
    "claude_command": TargetSpec(
        key="claude_command",
        host_suffix="claude",
        label="plugins/guia/commands/<verb>.md",
        name_of=lambda verb: verb,
        dir_of=lambda p: p.command_dir,
        emits_command=True,
    ),
}


def _target(target_name: str) -> TargetSpec:
    spec = TARGETS.get(target_name)
    if spec is None:
        raise ValueError(f"target desconhecido: {target_name}")
    return spec


# --- Loaders ---------------------------------------------------------------


def load_manifest(paths: Paths) -> dict:
    if not paths.manifest.exists():
        raise RenderError(f"Erro: manifest nao encontrado em {paths.manifest}")
    data = yaml.safe_load(paths.manifest.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict) or not data.get("verbs"):
        raise RenderError(
            "Erro: manifest invalido ou vazio (esperado mapping com chave `verbs:`)"
        )
    return data


def target_path(target: str, verb: str, paths: Paths) -> Path:
    return _target(target).output_path(verb, paths)


# Chaves de frontmatter sempre reservadas e geradas pelo renderer.
# Tentar override aborta (achado 4.11).
RESERVED_FRONTMATTER_KEYS = frozenset({"name", "description"})

# Frontmatter extras suportados (achado 4.11). Sao copiados verbatim
# para o frontmatter como `key: value` quando declarados em
# `verbs.<verb>.frontmatter` no manifest. Listas viram blocos YAML.
ALLOWED_EXTRA_KEYS = frozenset({"allowed-tools", "model"})


def _format_frontmatter_value(value: object) -> str:
    """Format a frontmatter value as a YAML scalar / inline list.

    Strings ficam plain; listas viram inline `[a, b, c]`; outros tipos
    sao convertidos para `yaml.safe_dump` flow style.
    """
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "[" + ", ".join(str(item) for item in value) + "]"
    return yaml.safe_dump(value, default_flow_style=True).strip().rstrip("...")


def render_skill_md(
    name: str,
    description: str,
    body: str,
    verb: str,
    extras: dict | None = None,
    include_name: bool = True,
) -> str:
    desc = description.strip()
    if not desc:
        raise RenderError(
            f"Erro: description vazio para verbo `{verb}` no manifest.\n"
            f"      Sem description o frontmatter da skill fica invalido."
        )
    body_text = dedent(body).strip("\n")
    if not body_text:
        sys.stderr.write(f"Aviso: body vazio para verbo `{verb}`. SKILL.md sera so frontmatter.\n")
    # Plugin commands do Claude derivam o nome do stem do arquivo, entao nao
    # levam `name:` no frontmatter; Agent Skills levam (include_name=True).
    lines = ["---"]
    if include_name:
        lines.append(f"name: {name}")
    lines.append(f"description: {desc}")
    if extras:
        for key, value in extras.items():
            if key in RESERVED_FRONTMATTER_KEYS:
                raise RenderError(
                    f"Erro: frontmatter.{key} (verbo `{verb}`) e reservado pelo renderer."
                )
            if key not in ALLOWED_EXTRA_KEYS:
                sys.stderr.write(
                    f"Aviso: frontmatter.{key} (verbo `{verb}`) nao esta na lista permitida ({sorted(ALLOWED_EXTRA_KEYS)}).\n"
                )
            lines.append(f"{key}: {_format_frontmatter_value(value)}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines) + "\n" + body_text + "\n"


def render_target(
    target: str,
    verb: str,
    description: str,
    body: str,
    extras: dict | None = None,
) -> str:
    spec = _target(target)
    return render_skill_md(
        spec.skill_name(verb),
        description,
        body,
        verb,
        extras,
        include_name=not spec.emits_command,
    )


# Match `{{include: path/to/file.md}}` on its own line. Partials sao
# resolvidos em build-time pelo renderer: o output em plugins/guia/ fica
# self-contained (nenhuma indirecao em runtime do agente).
INCLUDE_RE = re.compile(r"^\{\{include:\s*([^}\s][^}]*?)\s*\}\}$", re.MULTILINE)

# Match `{{include_per_target: path/to/base}}` on its own line. Resolvido
# em pre-processamento (antes do INCLUDE_RE) para um `{{include: ...}}`
# concreto baseado no target sendo renderizado:
#   agent_skill    -> base.agent.md
#   claude_command -> base.claude.md
# Permite consolidar bodies de verbo em um arquivo so quando o unico
# bit host-specific e qual partial de rename incluir (D-050).
INCLUDE_PER_TARGET_RE = re.compile(
    r"^\{\{include_per_target:\s*([^}\s][^}]*?)\s*\}\}$", re.MULTILINE
)


def _expand_per_target(text: str, target_name: str, origin: Path) -> str:
    """Pre-processa {{include_per_target: <base>}} em {{include: <base>.<host>.md}}.

    Roda **antes** de _expand_includes, entao o caminho gerado segue a
    semantica padrao do include (relativo ao arquivo que inclui). O sufixo
    do host vem do registro TARGETS; target desconhecido aborta.
    """
    spec = TARGETS.get(target_name)
    suffix = spec.host_suffix if spec else None
    if suffix is None and INCLUDE_PER_TARGET_RE.search(text):
        raise RenderError(
            f"Erro: target `{target_name}` (em {origin}) nao tem entrada em "
            f"TARGETS, mas o body usa {{{{include_per_target:}}}}."
        )

    def replace(match: re.Match[str]) -> str:
        base = match.group(1).strip()
        return f"{{{{include: {base}.{suffix}.md}}}}"

    return INCLUDE_PER_TARGET_RE.sub(replace, text)


def _expand_includes(
    text: str,
    origin: Path,
    manifest_dir: Path,
    body_cache: dict[Path, str],
    stack: tuple[Path, ...] = (),
) -> str:
    """Recursively expand `{{include: <path>}}` directives.

    Paths sao relativos ao **diretorio do arquivo que inclui** (semantica
    intuitiva: um body em `bodies/foo.md` que faz `{{include: _partials/x.md}}`
    pega `bodies/_partials/x.md`; um partial em `bodies/_partials/a.md` que
    faz `{{include: b.md}}` pega `bodies/_partials/b.md`). Guards:
      - file not found -> RenderError
      - path traversal (fora de manifest_dir) -> RenderError
      - include circular (path ja na pilha atual) -> RenderError

    `body_cache` evita re-leitura quando o mesmo partial aparece em
    bodies diferentes. A pilha (`stack`) detecta ciclo per-render-path
    sem poluir o cache.
    """
    base_dir = origin.parent
    root = manifest_dir.resolve()

    def replace(match: re.Match[str]) -> str:
        rel = match.group(1).strip()
        path = (base_dir / rel).resolve()
        if not str(path).startswith(str(root)):
            raise RenderError(
                f"Erro: include `{rel}` em {origin} aponta fora de core/manifest/ (path traversal recusado)."
            )
        if not path.exists():
            raise RenderError(
                f"Erro: include `{rel}` (em {origin}) nao existe em {path}."
            )
        if path in stack:
            chain = " -> ".join(str(p.relative_to(root)) for p in stack + (path,))
            raise RenderError(f"Erro: include circular detectado: {chain}")
        if path not in body_cache:
            body_cache[path] = path.read_text(encoding="utf-8")
        # Recursivo: partials podem incluir outros partials.
        return _expand_includes(
            body_cache[path].strip("\n"), path, manifest_dir, body_cache, stack + (path,)
        )

    return INCLUDE_RE.sub(replace, text)


def _resolve_body(
    verb: str,
    target_name: str,
    target_spec: dict,
    spec_shared_body: str | None,
    paths: Paths,
    body_cache: dict[Path, str],
) -> str:
    """Return the body for a target.

    Resolution order (v2 Layout B + F-019):
      1. target_spec['body_file'] explicit (per-target override)
      2. verb-level `shared_body:` field (covers all targets of the verb)
      3. legacy target_spec['body'] inline (v1 backward compat)

    `body_cache` evita re-leitura quando dois caminhos sao identicos.
    Includes `{{include: ...}}` e `{{include_per_target: ...}}` sao
    expandidos antes de retornar (o segundo vira o primeiro no
    pre-processamento, baseado em target_name).
    """
    manifest_dir = paths.manifest_dir
    explicit = target_spec.get("body_file")
    chosen = explicit or spec_shared_body
    if chosen:
        path = (manifest_dir / chosen).resolve()
        if not path.exists():
            raise RenderError(
                f"Erro: body_file `{chosen}` (de `{verb}.{target_name}`) nao existe em {path}."
            )
        if not str(path).startswith(str(manifest_dir.resolve())):
            raise RenderError(
                f"Erro: body_file `{chosen}` aponta fora de core/manifest/ (path traversal recusado)."
            )
        if path not in body_cache:
            body_cache[path] = path.read_text(encoding="utf-8")
        pre = _expand_per_target(body_cache[path], target_name, path)
        return _expand_includes(pre, path, manifest_dir, body_cache)
    body_inline = target_spec.get("body") or ""
    # Inline bodies tambem suportam includes; origin sintetica.
    origin = manifest_dir / f"<inline:{verb}.{target_name}>"
    pre = _expand_per_target(body_inline, target_name, origin)
    return _expand_includes(pre, origin, manifest_dir, body_cache)


def collect_outputs(
    manifest: dict, paths: Paths, only_verb: str | None = None
) -> list[Output]:
    outputs: list[Output] = []
    verbs = manifest.get("verbs") or {}
    body_cache: dict[Path, str] = {}
    for verb, spec in verbs.items():
        if only_verb and verb != only_verb:
            continue
        if not isinstance(spec, dict):
            raise RenderError(f"Erro: verb `{verb}` no manifest precisa ser um mapping.")
        description = (spec.get("description") or "").strip()
        shared_body = spec.get("shared_body")
        extras = spec.get("frontmatter")
        if extras is not None and not isinstance(extras, dict):
            raise RenderError(f"Erro: verbs.{verb}.frontmatter precisa ser um mapping.")
        targets = spec.get("targets") or {}
        if not targets:
            sys.stderr.write(f"Aviso: verbo `{verb}` sem `targets:` declarado.\n")
        for target_name, target_spec in targets.items():
            if not isinstance(target_spec, dict):
                raise RenderError(
                    f"Erro: targets.{target_name} de `{verb}` precisa ser um mapping."
                )
            body = _resolve_body(verb, target_name, target_spec, shared_body, paths, body_cache)
            content = render_target(target_name, verb, description, body, extras)
            outputs.append(Output(target_path(target_name, verb, paths), target_name, verb, content))
    return outputs


# --- bin/ -----------------------------------------------------------------


def _adapt_wrapper_for_plugin(text: str) -> str:
    """Reescreve o wrapper para o layout flat do plugin.

    No repo-mae, `core/bin/guia.ps1` resolve o motor via `..\\src\\guia.py`.
    No plugin/consumidor, `plugins/guia/bin/guia.ps1` e `plugins/guia/bin/guia.py` vivem
    lado a lado, entao o path vira `guia.py`. ABORTA se o marcador sumir,
    em vez do warning silencioso de antes (achado 4.3).
    """
    if WRAPPER_MARKER not in text:
        raise RenderError(
            f"Erro: core/bin/guia.ps1 nao contem o marcador `{WRAPPER_MARKER}`.\n"
            "      O renderer presume esse marker para adaptar o wrapper ao layout flat\n"
            "      do plugin. Se voce reescreveu o wrapper, ajuste WRAPPER_MARKER em\n"
            "      core/build/render-skills.py para o novo marker."
        )
    return text.replace(WRAPPER_MARKER, WRAPPER_REPLACEMENT)


def _python_source_files(paths: Paths) -> list[Path]:
    """All .py files in core/src/ (ai.py + helpers _*.py).

    Excludes __pycache__/ and the like. The whole pack is shipped flat to
    plugins/guia/bin/ so imports work side-by-side.
    """
    if not paths.core_src_dir.exists():
        raise RenderError(f"Erro: pasta de motor nao encontrada em {paths.core_src_dir}")
    return sorted(
        path
        for path in paths.core_src_dir.glob("*.py")
        if path.is_file() and not path.name.startswith("__")
    )


def collect_bin_outputs(paths: Paths) -> list[Output]:
    if not paths.engine_src.exists():
        raise RenderError(f"Erro: motor nao encontrado em {paths.engine_src}")
    if not paths.wrapper_src.exists():
        raise RenderError(f"Erro: wrapper nao encontrado em {paths.wrapper_src}")
    if not paths.lock_api_src.exists():
        raise RenderError(f"Erro: lock_api nao encontrado em {paths.lock_api_src}")
    if not paths.check_lock_src.exists():
        raise RenderError(f"Erro: check-lock nao encontrado em {paths.check_lock_src}")

    outputs: list[Output] = []
    for src in _python_source_files(paths):
        outputs.append(Output(paths.bin_dir / src.name, "bin", src.name, src.read_text(encoding="utf-8")))
    outputs.append(
        Output(paths.bin_dir / "lock_api.py", "bin", "lock_api.py", paths.lock_api_src.read_text(encoding="utf-8"))
    )
    # check-lock.py ships next to lock_api.py so the commit-msg hook of a
    # plugin-global consumer can run the validator from the plugin (D-076).
    # Kept as a verbatim copy; hyphen in the name is fine (run as a script,
    # never imported).
    outputs.append(
        Output(paths.bin_dir / "check-lock.py", "bin", "check-lock.py", paths.check_lock_src.read_text(encoding="utf-8"))
    )
    wrapper = _adapt_wrapper_for_plugin(paths.wrapper_src.read_text(encoding="utf-8"))
    outputs.append(Output(paths.bin_dir / "guia.ps1", "bin", "guia.ps1", wrapper))
    outputs.append(Output(paths.bin_dir / "guia", "bin", "guia", POSIX_SHIM))
    return outputs


# --- templates/ -----------------------------------------------------------


def _validate_template_set(paths: Paths) -> None:
    """Fail if core/templates/ has files not declared in TEMPLATE_FILES."""
    declared = {src for src, _dst in TEMPLATE_FILES}
    found: set[str] = set()
    for path in paths.templates_src.rglob("*"):
        if path.is_file():
            found.add(path.relative_to(paths.templates_src).as_posix())
    extras = found - declared
    if extras:
        raise RenderError(
            "Erro: arquivos em core/templates/ nao declarados em TEMPLATE_FILES:\n"
            + "\n".join(f"  - {x}" for x in sorted(extras))
        )


def _validate_template_yaml(src: Path) -> None:
    """yaml.safe_load templates antes de copiar (achado 7.7)."""
    if src.suffix not in (".yaml", ".yml"):
        return
    try:
        yaml.safe_load(src.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise RenderError(f"Erro: template YAML invalido em {src}: {exc}")


def collect_template_outputs(paths: Paths) -> list[Output]:
    _validate_template_set(paths)
    outputs: list[Output] = []
    for src_rel, dst_rel in TEMPLATE_FILES:
        src = paths.templates_src / src_rel
        if not src.exists():
            raise RenderError(f"Erro: template nao encontrado em {src}")
        _validate_template_yaml(src)
        content = src.read_text(encoding="utf-8")
        outputs.append(Output(paths.templates_dir / dst_rel, "template", dst_rel, content))
    # Templates promovidos de fora de core/templates/ (achado 6.Q1).
    for rel, dst_rel in PROMOTED_TEMPLATES:
        src = paths.root.joinpath(*rel)
        if not src.exists():
            raise RenderError(f"Erro: template promovido nao encontrado em {src}")
        content = src.read_text(encoding="utf-8")
        outputs.append(Output(paths.templates_dir / dst_rel, "template", dst_rel, content))
    return outputs


# --- I/O ------------------------------------------------------------------


def write_outputs(outputs: list[Output]) -> list[Path]:
    written: list[Path] = []
    for output in outputs:
        output.path.parent.mkdir(parents=True, exist_ok=True)
        current = output.path.read_text(encoding="utf-8") if output.path.exists() else None
        if current != output.content:
            output.path.write_text(output.content, encoding="utf-8", newline="\n")
            written.append(output.path)
    return written


def check_outputs(outputs: list[Output]) -> list[Path]:
    stale: list[Path] = []
    for output in outputs:
        current = output.path.read_text(encoding="utf-8") if output.path.exists() else None
        if current != output.content:
            stale.append(output.path)
    return stale


# --- Orphan detection (--check-orphans) -----------------------------------


# Caches/artefatos transientes que aparecem em plugins/guia/ por uso (ex.: rodar
# o motor standalone gera __pycache__) e nao devem ser tratados como
# orfaos do renderer.
ORPHAN_IGNORE_DIR_NAMES = frozenset({"__pycache__", ".pytest_cache", ".mypy_cache"})

# Partials viven em core/manifest/bodies/_partials/ - sao usados via
# `{{include: ...}}` mas nao sao alvos diretos de render. O renderer
# nao copia partials para plugins/guia/ (eles ja foram expandidos in-place no
# body do verbo que os consumiu). Esse marcador documenta a convencao.
PARTIAL_DIR_NAME = "_partials"


def _is_ignored_for_orphan(path: Path) -> bool:
    return any(part in ORPHAN_IGNORE_DIR_NAMES for part in path.parts)


def find_orphans(outputs: list[Output], paths: Paths) -> list[Path]:
    """List files in plugins/guia/bin/, commands/ and .agents/skills/ not part of outputs.

    Useful to detect verb removals or renamed helpers that left stale
    files in plugins/guia/. Renderer itself does not delete unless --clean.
    Ignora __pycache__/.pytest_cache/.mypy_cache.
    """
    expected = {output.path.resolve() for output in outputs}
    orphans: list[Path] = []
    for root in (paths.bin_dir, paths.command_dir, paths.agent_skill_dir, paths.templates_dir):
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if _is_ignored_for_orphan(path):
                continue
            if path.resolve() not in expected:
                orphans.append(path)
    return orphans


def clean_orphans(outputs: list[Output], paths: Paths) -> list[Path]:
    """Apaga arquivos orfaos retornados por `find_orphans` (achado 4.Q3).

    Tambem remove diretorios que ficaram vazios apos a limpeza para que
    `plugins/guia/.agents/skills/<guia-verbo-removido>/` desapareca quando seu
    unico SKILL.md e removido (os commands do Claude sao arquivos flat).

    Retorna a lista de paths apagados.
    """
    orphans = find_orphans(outputs, paths)
    removed: list[Path] = []
    for path in orphans:
        try:
            path.unlink()
            removed.append(path)
        except OSError as exc:
            sys.stderr.write(f"Aviso: nao consegui apagar {path}: {exc}\n")
    # Limpeza de diretorios vazios (bottom-up)
    for root in (paths.command_dir, paths.agent_skill_dir, paths.templates_dir, paths.bin_dir):
        if not root.exists():
            continue
        # Bottom-up: rglob retorna nested-first quando reverse-sort
        for path in sorted(root.rglob("*"), key=lambda p: -len(p.parts)):
            if path.is_dir() and not any(path.iterdir()):
                try:
                    path.rmdir()
                except OSError:
                    pass
    return removed


# --- Entry point ----------------------------------------------------------


def _rel(path: Path, root: Path) -> str:
    """Path relativo a root quando possivel; absoluto caso contrario."""
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def collect_all_outputs(paths: Paths, only_verb: str | None) -> list[Output]:
    """Skills do manifest + (quando full render) bin/ e templates/."""
    outputs = collect_outputs(load_manifest(paths), paths, only_verb=only_verb)
    if not only_verb:
        outputs = outputs + collect_bin_outputs(paths) + collect_template_outputs(paths)
    return outputs


def _run_check_orphans(outputs: list[Output], paths: Paths) -> int:
    orphans = find_orphans(outputs, paths)
    if not orphans:
        print("OK: nenhum orfao em plugins/guia/.")
        return 0
    print("Arquivos orfaos (em plugins/guia/ sem origem no manifest/motor):\n", file=sys.stderr)
    for path in orphans:
        print(f"  - {_rel(path, paths.root)}", file=sys.stderr)
    return 1


def _run_check(outputs: list[Output], paths: Paths) -> int:
    stale = check_outputs(outputs)
    if stale:
        print(
            "Arquivos gerados estao desatualizados em relacao ao manifest/motor/wrapper:\n",
            file=sys.stderr,
        )
        for p in stale:
            print(f"  - {_rel(p, paths.root)}", file=sys.stderr)
        print("\nRode: python core/build/render-skills.py", file=sys.stderr)
        return 1
    print(f"OK: {len(outputs)} alvo(s) em sincronia com o manifest.")
    return 0


def _run_render(outputs: list[Output], paths: Paths, do_clean: bool) -> int:
    written = write_outputs(outputs)
    cleaned = clean_orphans(outputs, paths) if do_clean else []
    if not written and not cleaned:
        print(f"OK: {len(outputs)} alvo(s) ja estavam atualizados. Nada gravado.")
        return 0
    if written:
        print(f"Renderizados {len(written)} arquivo(s) de {len(outputs)} alvo(s):")
        for p in written:
            print(f"  + {_rel(p, paths.root)}")
    if cleaned:
        print(f"Apagados {len(cleaned)} arquivo(s) orfao(s):")
        for p in cleaned:
            print(f"  - {_rel(p, paths.root)}")
    return 0


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Exit 1 se algum alvo estiver stale.")
    parser.add_argument("--verb", help="Renderiza apenas um verbo do manifest (pula plugins/guia/bin/).")
    parser.add_argument(
        "--check-orphans",
        action="store_true",
        help="Lista arquivos em plugins/guia/ sem correspondente no manifest/motor (nao apaga).",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Apaga arquivos orfaos em plugins/guia/ apos renderizar (cuidado).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Sobrescreve destino plugins/guia/ (default: <repo>/plugins/guia/).",
    )
    return parser


def _dispatch(args: argparse.Namespace, paths: Paths) -> int:
    outputs = collect_all_outputs(paths, args.verb)
    if not outputs:
        sys.stderr.write("Aviso: nenhum alvo a renderizar (manifest vazio ou --verb nao bate).\n")
        return 0
    if args.check_orphans:
        return _run_check_orphans(outputs, paths)
    if args.check:
        return _run_check(outputs, paths)
    return _run_render(outputs, paths, args.clean)


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    paths = Paths.build(ROOT, dist_dir=args.output_dir)
    try:
        return _dispatch(args, paths)
    except RenderError as exc:
        message = str(exc)
        if not message.endswith("\n"):
            message += "\n"
        sys.stderr.write(message)
        return 2


if __name__ == "__main__":
    sys.exit(main())
