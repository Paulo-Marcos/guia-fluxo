#!/usr/bin/env python3
"""Render per-agent skill files and standalone bin/ from core/manifest/manifest.yaml.

Source of truth:
    core/manifest/manifest.yaml  (skills)
    core/src/ai.py               (motor copiado para dist/bin/)
    core/bin/ai.ps1              (wrapper PowerShell copiado para dist/bin/)

Generated targets (por verbo):
    dist/skills/<verb>/SKILL.md             (Claude Code - layout oficial de plugin, sem prefixo: o namespace `ai:` ja qualifica os atalhos como /ai:feature, /ai:issue, etc.)
    dist/.agents/skills/ai-<verb>/SKILL.md  (Codex + Antigravity - convencao AGENTS.md cross-tool. Prefixo `ai-` evita colisao com comandos nativos do agente. Verbos que ja comecam com `ai-` - como `ai-process` - nao recebem o prefixo de novo.)

Generated bin/ (motor standalone do plugin):
    dist/bin/ai.py    (copia exata de core/src/ai.py)
    dist/bin/ai.ps1   (copia de core/bin/ai.ps1 com path adaptado para layout flat)
    dist/bin/ai       (shim POSIX que chama python3 ai.py "$@")

Generated templates/ (consumiveis pelo instalador install.ps1/install.sh):
    dist/templates/.githooks/commit-msg
    dist/templates/features/registry.yaml
    dist/templates/features/lock-ignore.txt

dist/ espelha o layout que o consumidor recebe: marketplace.json/plugin.json
em `dist/.claude-plugin/` apontam para o plugin com root `dist/`. O `dist/bin/`
e auto-mapeado para PATH pelo Claude Code segundo a doc oficial, entao no
consumidor (apos B-008 copiar dist/* para .ai-process/) basta digitar `ai status`
em qualquer sessao do agente.

Codex + Antigravity continuam descobrindo via `dist/.agents/skills/ai-<verb>/`
seguindo a convencao AGENTS.md. Detalhes em
docs/adr/0006-plugin-oficial-claude-code.md.

Usage:
    python core/build/render-skills.py            # write all targets (skills + bin/)
    python core/build/render-skills.py --check    # exit 1 if any target is stale
    python core/build/render-skills.py --verb X   # render only one verb (skip bin/)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from textwrap import dedent

try:
    import yaml
except ImportError:
    sys.stderr.write("Erro: PyYAML nao instalado. Rode: pip install pyyaml\n")
    sys.exit(2)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "core" / "manifest" / "manifest.yaml"
DIST_DIR = ROOT / "dist"
CLAUDE_SKILL_DIR = DIST_DIR / "skills"
AGENT_SKILL_DIR = DIST_DIR / ".agents" / "skills"
BIN_DIR = DIST_DIR / "bin"
TEMPLATES_DIR = DIST_DIR / "templates"
ENGINE_SRC = ROOT / "core" / "src" / "ai.py"
WRAPPER_SRC = ROOT / "core" / "bin" / "ai.ps1"
TEMPLATES_SRC = ROOT / "core" / "templates"

# Cada par e (caminho relativo dentro de core/templates/, caminho relativo
# dentro de dist/templates/). Mantemos paridade 1:1 para o instalador
# consumir sem aplanar a arvore.
TEMPLATE_FILES = [
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

# Shim POSIX para o plugin: roda o motor Python da mesma pasta.
POSIX_SHIM = (
    "#!/usr/bin/env bash\n"
    "# Auto-gerado por core/build/render-skills.py. Nao edite.\n"
    'exec python3 "$(dirname "$0")/ai.py" "$@"\n'
)


def load_manifest() -> dict:
    if not MANIFEST.exists():
        sys.stderr.write(f"Erro: manifest nao encontrado em {MANIFEST}\n")
        sys.exit(2)
    return yaml.safe_load(MANIFEST.read_text(encoding="utf-8")) or {}


def agent_skill_name(verb: str) -> str:
    """Nome do skill no destino cross-tool (Codex/Antigravity).

    Aplica prefixo `ai-` para evitar colisao com comandos nativos do agente.
    Verbos que ja comecam com `ai-` (ex.: `ai-process`) ficam inalterados
    em vez de virar `ai-ai-process`.
    """
    return verb if verb.startswith("ai-") else f"ai-{verb}"


def target_path(target: str, verb: str) -> Path:
    if target == "agent_skill":
        return AGENT_SKILL_DIR / agent_skill_name(verb) / "SKILL.md"
    if target == "claude_skill":
        return CLAUDE_SKILL_DIR / verb / "SKILL.md"
    raise ValueError(f"target desconhecido: {target}")


def render_skill_md(name: str, description: str, body: str) -> str:
    desc = description.strip()
    body_text = dedent(body).strip("\n")
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
        return render_skill_md(agent_skill_name(verb), description, body)
    if target == "claude_skill":
        return render_skill_md(verb, description, body)
    raise ValueError(f"target desconhecido: {target}")


def collect_outputs(manifest: dict, only_verb: str | None = None) -> list[tuple[Path, str, str, str]]:
    """Return list of (path, target, verb, content) tuples for skills."""
    outputs: list[tuple[Path, str, str, str]] = []
    verbs = manifest.get("verbs") or {}
    for verb, spec in verbs.items():
        if only_verb and verb != only_verb:
            continue
        description = (spec.get("description") or "").strip()
        targets = spec.get("targets") or {}
        for target_name, target_spec in targets.items():
            body = target_spec.get("body") or ""
            content = render_target(target_name, verb, description, body)
            outputs.append((target_path(target_name, verb), target_name, verb, content))
    return outputs


def _adapt_wrapper_for_plugin(text: str) -> str:
    """Reescreve o wrapper para o layout flat do plugin.

    No repo-mae, `core/bin/ai.ps1` resolve o motor via `..\\src\\ai.py`.
    No plugin/consumidor, `dist/bin/ai.ps1` e `dist/bin/ai.py` vivem lado a
    lado (mesma pasta), entao o path vira `ai.py` relativo a $PSScriptRoot.
    """
    if "..\\src\\ai.py" not in text:
        sys.stderr.write(
            "Aviso: core/bin/ai.ps1 nao contem o marcador '..\\src\\ai.py'. "
            "O renderer precisa ser revisado.\n"
        )
    return text.replace("..\\src\\ai.py", "ai.py")


def collect_bin_outputs() -> list[tuple[Path, str, str, str]]:
    """Return list of (path, target, name, content) tuples for dist/bin/."""
    if not ENGINE_SRC.exists():
        sys.stderr.write(f"Erro: motor nao encontrado em {ENGINE_SRC}\n")
        sys.exit(2)
    if not WRAPPER_SRC.exists():
        sys.stderr.write(f"Erro: wrapper nao encontrado em {WRAPPER_SRC}\n")
        sys.exit(2)
    engine = ENGINE_SRC.read_text(encoding="utf-8")
    wrapper = _adapt_wrapper_for_plugin(WRAPPER_SRC.read_text(encoding="utf-8"))
    return [
        (BIN_DIR / "ai.py", "bin", "ai.py", engine),
        (BIN_DIR / "ai.ps1", "bin", "ai.ps1", wrapper),
        (BIN_DIR / "ai", "bin", "ai", POSIX_SHIM),
    ]


def collect_template_outputs() -> list[tuple[Path, str, str, str]]:
    """Return list of (path, target, name, content) tuples for dist/templates/.

    Templates ficam em `dist/templates/` espelhando o layout em que o
    instalador vai depositar no consumidor (`<consumer>/.githooks/`,
    `<consumer>/features/`). Copia byte-a-byte de `core/templates/`.
    """
    outputs: list[tuple[Path, str, str, str]] = []
    for src_rel, dst_rel in TEMPLATE_FILES:
        src = TEMPLATES_SRC / src_rel
        if not src.exists():
            sys.stderr.write(f"Erro: template nao encontrado em {src}\n")
            sys.exit(2)
        content = src.read_text(encoding="utf-8")
        outputs.append((TEMPLATES_DIR / dst_rel, "template", dst_rel, content))
    return outputs


def write_outputs(outputs: list[tuple[Path, str, str, str]]) -> list[Path]:
    written: list[Path] = []
    for path, _target, _name, content in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != content:
            # newline="\n" evita que Python traduza \n -> \r\n no Windows.
            # Critico para dist/bin/ai (shim bash precisa de LF puro) e
            # coerente com a normalizacao de .gitattributes (eol=lf default).
            # Wrappers/scripts .ps1 sao re-normalizados para CRLF no checkout
            # via *.ps1 -> eol=crlf, entao gravar em LF aqui e seguro.
            path.write_text(content, encoding="utf-8", newline="\n")
            written.append(path)
    return written


def check_outputs(outputs: list[tuple[Path, str, str, str]]) -> list[Path]:
    stale: list[Path] = []
    for path, _target, _name, content in outputs:
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != content:
            stale.append(path)
    return stale


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Exit 1 se algum alvo estiver stale (uso em CI).")
    parser.add_argument("--verb", help="Renderiza apenas um verbo do manifest (pula dist/bin/).")
    args = parser.parse_args()

    manifest = load_manifest()
    outputs = collect_outputs(manifest, only_verb=args.verb)
    if not args.verb:
        outputs = outputs + collect_bin_outputs() + collect_template_outputs()

    if not outputs:
        sys.stderr.write("Aviso: nenhum alvo a renderizar (manifest vazio ou --verb nao bate).\n")
        return 0

    if args.check:
        stale = check_outputs(outputs)
        if stale:
            print("Arquivos gerados estao desatualizados em relacao ao manifest/motor/wrapper:\n", file=sys.stderr)
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
