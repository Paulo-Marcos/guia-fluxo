#!/usr/bin/env python3
"""Render per-agent skill files and standalone bin/ from core/manifest/manifest.yaml.

Source of truth:
    core/manifest/manifest.yaml   (skills index: verbs + descriptions + body refs)
    core/manifest/bodies/*.md     (skill bodies - Layout B, F-016)
    core/src/*.py                 (motor + helpers - todos copiados para dist/bin/)
    core/lock/lock_api.py         (modulo de locks reutilizavel - tambem em dist/bin/)
    core/bin/ai.ps1               (wrapper PowerShell copiado para dist/bin/)
    core/templates/...            (templates copiados para dist/templates/)

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
          claude_skill:
            body_file: bodies/<verb>.claude.md

    Para shared body entre targets, aponte ambos para o mesmo arquivo.

Generated targets (por verbo):
    dist/skills/<verb>/SKILL.md             (Claude Code - layout oficial de plugin)
    dist/.agents/skills/ai-<verb>/SKILL.md  (Codex + Antigravity - prefixo `ai-`)

Generated bin/ (motor standalone do plugin):
    dist/bin/ai.py        (entry point, copia exata de core/src/ai.py)
    dist/bin/_*.py        (modulos sibling: _constants, _state, _tasks, etc.)
    dist/bin/lock_api.py  (lock domain - copiado de core/lock/lock_api.py)
    dist/bin/ai.ps1       (copia de core/bin/ai.ps1 com path adaptado para layout flat)
    dist/bin/ai           (shim POSIX que chama python3 ai.py "$@")

Generated templates/:
    dist/templates/.githooks/commit-msg
    dist/templates/features/registry.yaml
    dist/templates/features/lock-ignore.txt

Hardening (F-015):
- TEMPLATE_FILES validado: --check detecta arquivos em core/templates/ nao listados.
- Renderer aborta (sys.exit 2) se o marcador `..\\src\\ai.py` sumir do wrapper.
- YAML dos templates e validado via yaml.safe_load antes de copiar.
- dataclass Output substitui a tupla de 4 elementos.
- --check-orphans lista arquivos em dist/bin/ ou dist/skills/ sem correspondente.
- Description vazia gera erro explicito em vez de SKILL.md silenciosamente quebrado.

Usage:
    python core/build/render-skills.py
    python core/build/render-skills.py --check
    python core/build/render-skills.py --verb feature
    python core/build/render-skills.py --check-orphans
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent

try:
    import yaml
except ImportError:
    sys.stderr.write("Erro: PyYAML nao instalado. Rode: pip install pyyaml\n")
    sys.exit(2)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_DIR = ROOT / "core" / "manifest"
MANIFEST = MANIFEST_DIR / "manifest.yaml"
BODIES_DIR = MANIFEST_DIR / "bodies"
DIST_DIR = ROOT / "dist"
CLAUDE_SKILL_DIR = DIST_DIR / "skills"
AGENT_SKILL_DIR = DIST_DIR / ".agents" / "skills"
BIN_DIR = DIST_DIR / "bin"
TEMPLATES_DIR = DIST_DIR / "templates"

CORE_SRC_DIR = ROOT / "core" / "src"
ENGINE_SRC = CORE_SRC_DIR / "ai.py"
LOCK_API_SRC = ROOT / "core" / "lock" / "lock_api.py"
WRAPPER_SRC = ROOT / "core" / "bin" / "ai.ps1"
TEMPLATES_SRC = ROOT / "core" / "templates"

# Marcador usado por core/bin/ai.ps1 para resolver o motor. No dist/, o
# layout vira flat (ai.py vizinho do wrapper), entao o marcador e
# reescrito. Aborta se ausente: o renderer presume invariante.
WRAPPER_MARKER = "..\\src\\ai.py"
WRAPPER_REPLACEMENT = "ai.py"

# Templates copiados byte-a-byte para dist/templates/. Validacao
# estrutural por extensao: arquivos .yaml passam por yaml.safe_load.
TEMPLATE_FILES: list[tuple[str, str]] = [
    (".githooks/commit-msg", ".githooks/commit-msg"),
    ("features/registry.yaml", "features/registry.yaml"),
    ("features/lock-ignore.txt", "features/lock-ignore.txt"),
]

TARGET_LABELS = {
    "agent_skill": "dist/.agents/skills/ai-<verb>/SKILL.md",
    "claude_skill": "dist/skills/<verb>/SKILL.md",
    "bin": "dist/bin/<file>",
    "template": "dist/templates/<file>",
}

POSIX_SHIM = (
    "#!/usr/bin/env bash\n"
    "# Auto-gerado por core/build/render-skills.py. Nao edite.\n"
    'exec python3 "$(dirname "$0")/ai.py" "$@"\n'
)


@dataclass(frozen=True)
class Output:
    path: Path
    target: str
    name: str
    content: str


# --- Loaders ---------------------------------------------------------------


def load_manifest() -> dict:
    if not MANIFEST.exists():
        sys.stderr.write(f"Erro: manifest nao encontrado em {MANIFEST}\n")
        sys.exit(2)
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict) or not data.get("verbs"):
        sys.stderr.write(
            "Erro: manifest invalido ou vazio (esperado mapping com chave `verbs:`)\n"
        )
        sys.exit(2)
    return data


def agent_skill_name(verb: str) -> str:
    return verb if verb.startswith("ai-") else f"ai-{verb}"


def target_path(target: str, verb: str) -> Path:
    if target == "agent_skill":
        return AGENT_SKILL_DIR / agent_skill_name(verb) / "SKILL.md"
    if target == "claude_skill":
        return CLAUDE_SKILL_DIR / verb / "SKILL.md"
    raise ValueError(f"target desconhecido: {target}")


def render_skill_md(name: str, description: str, body: str, verb: str) -> str:
    desc = description.strip()
    if not desc:
        sys.stderr.write(
            f"Erro: description vazio para verbo `{verb}` no manifest.\n"
            f"      Sem description o frontmatter da skill fica invalido.\n"
        )
        sys.exit(2)
    body_text = dedent(body).strip("\n")
    if not body_text:
        sys.stderr.write(f"Aviso: body vazio para verbo `{verb}`. SKILL.md sera so frontmatter.\n")
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {desc}\n"
        "---\n"
        "\n"
        f"{body_text}\n"
    )


def render_target(target: str, verb: str, description: str, body: str) -> str:
    if target == "agent_skill":
        return render_skill_md(agent_skill_name(verb), description, body, verb)
    if target == "claude_skill":
        return render_skill_md(verb, description, body, verb)
    raise ValueError(f"target desconhecido: {target}")


def _resolve_body(verb: str, target_name: str, target_spec: dict, body_cache: dict[Path, str]) -> str:
    """Return the body for a target, resolving body_file with caching.

    Layout B (v2): `body_file: bodies/<verb>.<target>.md` relativo a
    core/manifest/. Layout A (v1, legacy): `body: |` inline. Suportamos
    os dois para migracao gradual; abortamos se o arquivo nao existir.

    `body_cache` permite que dois targets apontando para o MESMO arquivo
    leiam uma unica vez (shared_body trivial).
    """
    body_file = target_spec.get("body_file")
    if body_file:
        path = (MANIFEST_DIR / body_file).resolve()
        if not path.exists():
            sys.stderr.write(
                f"Erro: body_file `{body_file}` (de `{verb}.{target_name}`) nao existe em {path}.\n"
            )
            sys.exit(2)
        if not str(path).startswith(str(MANIFEST_DIR.resolve())):
            sys.stderr.write(
                f"Erro: body_file `{body_file}` aponta fora de core/manifest/ (path traversal recusado).\n"
            )
            sys.exit(2)
        if path not in body_cache:
            body_cache[path] = path.read_text(encoding="utf-8")
        return body_cache[path]
    return target_spec.get("body") or ""


def collect_outputs(manifest: dict, only_verb: str | None = None) -> list[Output]:
    outputs: list[Output] = []
    verbs = manifest.get("verbs") or {}
    body_cache: dict[Path, str] = {}
    for verb, spec in verbs.items():
        if only_verb and verb != only_verb:
            continue
        if not isinstance(spec, dict):
            sys.stderr.write(f"Erro: verb `{verb}` no manifest precisa ser um mapping.\n")
            sys.exit(2)
        description = (spec.get("description") or "").strip()
        targets = spec.get("targets") or {}
        if not targets:
            sys.stderr.write(f"Aviso: verbo `{verb}` sem `targets:` declarado.\n")
        for target_name, target_spec in targets.items():
            if not isinstance(target_spec, dict):
                sys.stderr.write(
                    f"Erro: targets.{target_name} de `{verb}` precisa ser um mapping.\n"
                )
                sys.exit(2)
            body = _resolve_body(verb, target_name, target_spec, body_cache)
            content = render_target(target_name, verb, description, body)
            outputs.append(Output(target_path(target_name, verb), target_name, verb, content))
    return outputs


# --- bin/ -----------------------------------------------------------------


def _adapt_wrapper_for_plugin(text: str) -> str:
    """Reescreve o wrapper para o layout flat do plugin.

    No repo-mae, `core/bin/ai.ps1` resolve o motor via `..\\src\\ai.py`.
    No plugin/consumidor, `dist/bin/ai.ps1` e `dist/bin/ai.py` vivem
    lado a lado, entao o path vira `ai.py`. ABORTA se o marcador sumir,
    em vez do warning silencioso de antes (achado 4.3).
    """
    if WRAPPER_MARKER not in text:
        sys.stderr.write(
            f"Erro: core/bin/ai.ps1 nao contem o marcador `{WRAPPER_MARKER}`.\n"
            "      O renderer presume esse marker para adaptar o wrapper ao layout flat\n"
            "      do plugin. Se voce reescreveu o wrapper, ajuste WRAPPER_MARKER em\n"
            "      core/build/render-skills.py para o novo marker.\n"
        )
        sys.exit(2)
    return text.replace(WRAPPER_MARKER, WRAPPER_REPLACEMENT)


def _python_source_files() -> list[Path]:
    """All .py files in core/src/ (ai.py + helpers _*.py).

    Excludes __pycache__/ and the like. The whole pack is shipped flat to
    dist/bin/ so imports work side-by-side.
    """
    if not CORE_SRC_DIR.exists():
        sys.stderr.write(f"Erro: pasta de motor nao encontrada em {CORE_SRC_DIR}\n")
        sys.exit(2)
    files = sorted(
        path
        for path in CORE_SRC_DIR.glob("*.py")
        if path.is_file() and not path.name.startswith("__")
    )
    return files


def collect_bin_outputs() -> list[Output]:
    if not ENGINE_SRC.exists():
        sys.stderr.write(f"Erro: motor nao encontrado em {ENGINE_SRC}\n")
        sys.exit(2)
    if not WRAPPER_SRC.exists():
        sys.stderr.write(f"Erro: wrapper nao encontrado em {WRAPPER_SRC}\n")
        sys.exit(2)
    if not LOCK_API_SRC.exists():
        sys.stderr.write(f"Erro: lock_api nao encontrado em {LOCK_API_SRC}\n")
        sys.exit(2)

    outputs: list[Output] = []
    for src in _python_source_files():
        outputs.append(Output(BIN_DIR / src.name, "bin", src.name, src.read_text(encoding="utf-8")))
    outputs.append(
        Output(BIN_DIR / "lock_api.py", "bin", "lock_api.py", LOCK_API_SRC.read_text(encoding="utf-8"))
    )
    wrapper = _adapt_wrapper_for_plugin(WRAPPER_SRC.read_text(encoding="utf-8"))
    outputs.append(Output(BIN_DIR / "ai.ps1", "bin", "ai.ps1", wrapper))
    outputs.append(Output(BIN_DIR / "ai", "bin", "ai", POSIX_SHIM))
    return outputs


# --- templates/ -----------------------------------------------------------


def _validate_template_set() -> None:
    """Fail if core/templates/ has files not declared in TEMPLATE_FILES."""
    declared = {src for src, _dst in TEMPLATE_FILES}
    found: set[str] = set()
    for path in TEMPLATES_SRC.rglob("*"):
        if path.is_file():
            rel = path.relative_to(TEMPLATES_SRC).as_posix()
            found.add(rel)
    extras = found - declared
    if extras:
        sys.stderr.write(
            "Erro: arquivos em core/templates/ nao declarados em TEMPLATE_FILES:\n"
            + "\n".join(f"  - {x}" for x in sorted(extras))
            + "\n"
        )
        sys.exit(2)


def _validate_template_yaml(src: Path) -> None:
    """yaml.safe_load templates antes de copiar (achado 7.7)."""
    if src.suffix not in (".yaml", ".yml"):
        return
    try:
        yaml.safe_load(src.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        sys.stderr.write(f"Erro: template YAML invalido em {src}: {exc}\n")
        sys.exit(2)


def collect_template_outputs() -> list[Output]:
    _validate_template_set()
    outputs: list[Output] = []
    for src_rel, dst_rel in TEMPLATE_FILES:
        src = TEMPLATES_SRC / src_rel
        if not src.exists():
            sys.stderr.write(f"Erro: template nao encontrado em {src}\n")
            sys.exit(2)
        _validate_template_yaml(src)
        content = src.read_text(encoding="utf-8")
        outputs.append(Output(TEMPLATES_DIR / dst_rel, "template", dst_rel, content))
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


def find_orphans(outputs: list[Output]) -> list[Path]:
    """List files in dist/bin/ and dist/skills/ that are not part of outputs.

    Useful to detect verb removals or renamed helpers that left stale
    files in dist/. Renderer itself does not delete; only reports.
    """
    expected = {output.path.resolve() for output in outputs}
    orphans: list[Path] = []
    for root in (BIN_DIR, CLAUDE_SKILL_DIR, AGENT_SKILL_DIR, TEMPLATES_DIR):
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.resolve() not in expected:
                orphans.append(path)
    return orphans


# --- Entry point ----------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Exit 1 se algum alvo estiver stale.")
    parser.add_argument("--verb", help="Renderiza apenas um verbo do manifest (pula dist/bin/).")
    parser.add_argument(
        "--check-orphans",
        action="store_true",
        help="Lista arquivos em dist/ sem correspondente no manifest/motor (nao apaga).",
    )
    args = parser.parse_args()

    manifest = load_manifest()
    outputs = collect_outputs(manifest, only_verb=args.verb)
    if not args.verb:
        outputs = outputs + collect_bin_outputs() + collect_template_outputs()

    if not outputs:
        sys.stderr.write("Aviso: nenhum alvo a renderizar (manifest vazio ou --verb nao bate).\n")
        return 0

    if args.check_orphans:
        orphans = find_orphans(outputs)
        if not orphans:
            print("OK: nenhum orfao em dist/.")
            return 0
        print("Arquivos orfaos (em dist/ sem origem no manifest/motor):\n", file=sys.stderr)
        for path in orphans:
            print(f"  - {path.relative_to(ROOT)}", file=sys.stderr)
        return 1

    if args.check:
        stale = check_outputs(outputs)
        if stale:
            print(
                "Arquivos gerados estao desatualizados em relacao ao manifest/motor/wrapper:\n",
                file=sys.stderr,
            )
            for p in stale:
                print(f"  - {p.relative_to(ROOT)}", file=sys.stderr)
            print("\nRode: python core/build/render-skills.py", file=sys.stderr)
            return 1
        print(f"OK: {len(outputs)} alvo(s) em sincronia com o manifest.")
        return 0

    written = write_outputs(outputs)
    if not written:
        print(f"OK: {len(outputs)} alvo(s) ja estavam atualizados. Nada gravado.")
        return 0
    print(f"Renderizados {len(written)} arquivo(s) de {len(outputs)} alvo(s):")
    for p in written:
        print(f"  + {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
