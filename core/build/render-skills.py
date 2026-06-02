#!/usr/bin/env python3
"""Render per-agent skill files from core/manifest/manifest.yaml.

Source of truth:
    core/manifest/manifest.yaml

Generated targets (per verb):
    dist/skills/<verb>/SKILL.md          (Claude Code - layout oficial de plugin)
    dist/.agents/skills/<verb>/SKILL.md  (Codex + Antigravity - convencao AGENTS.md cross-tool)

dist/ espelha o layout que o consumidor recebe: marketplace.json/plugin.json
em `dist/.claude-plugin/` apontam para o plugin com root `dist/`, entao Claude
descobre `dist/skills/<verb>/SKILL.md` e os atalhos saem como `/ai:feature`,
`/ai:issue`, etc. Codex + Antigravity continuam descobrindo via
`dist/.agents/skills/<verb>/` seguindo a convencao AGENTS.md.

A instalacao em outro projeto e tratada nos passos posteriores do refactor
(B-008/B-009) que copiam dist/ inteiro pro consumidor. Detalhes em
docs/adr/0006-plugin-oficial-claude-code.md.

Usage:
    python core/build/render-skills.py            # write all targets
    python core/build/render-skills.py --check    # exit 1 if any target is stale
    python core/build/render-skills.py --verb X   # render only one verb
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

TARGET_LABELS = {
    "agent_skill": "dist/.agents/skills/<verb>/SKILL.md",
    "claude_skill": "dist/skills/<verb>/SKILL.md",
}


def load_manifest() -> dict:
    if not MANIFEST.exists():
        sys.stderr.write(f"Erro: manifest nao encontrado em {MANIFEST}\n")
        sys.exit(2)
    return yaml.safe_load(MANIFEST.read_text(encoding="utf-8")) or {}


def target_path(target: str, verb: str) -> Path:
    if target == "agent_skill":
        return AGENT_SKILL_DIR / verb / "SKILL.md"
    if target == "claude_skill":
        return CLAUDE_SKILL_DIR / verb / "SKILL.md"
    raise ValueError(f"target desconhecido: {target}")


def render_skill_md(verb: str, description: str, body: str) -> str:
    desc = description.strip()
    body_text = dedent(body).strip("\n")
    return (
        "---\n"
        f"name: {verb}\n"
        f"description: {desc}\n"
        "---\n"
        "\n"
        f"{body_text}\n"
    )


def render_target(target: str, verb: str, description: str, body: str) -> str:
    if target in ("agent_skill", "claude_skill"):
        return render_skill_md(verb, description, body)
    raise ValueError(f"target desconhecido: {target}")


def collect_outputs(manifest: dict, only_verb: str | None = None) -> list[tuple[Path, str, str, str]]:
    """Return list of (path, target, verb, content) tuples."""
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


def write_outputs(outputs: list[tuple[Path, str, str, str]]) -> list[Path]:
    written: list[Path] = []
    for path, _target, _verb, content in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != content:
            path.write_text(content, encoding="utf-8")
            written.append(path)
    return written


def check_outputs(outputs: list[tuple[Path, str, str, str]]) -> list[Path]:
    stale: list[Path] = []
    for path, _target, _verb, content in outputs:
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != content:
            stale.append(path)
    return stale


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Exit 1 se algum alvo estiver stale (uso em CI).")
    parser.add_argument("--verb", help="Renderiza apenas um verbo do manifest.")
    args = parser.parse_args()

    manifest = load_manifest()
    outputs = collect_outputs(manifest, only_verb=args.verb)

    if not outputs:
        sys.stderr.write("Aviso: nenhum alvo a renderizar (manifest vazio ou --verb nao bate).\n")
        return 0

    if args.check:
        stale = check_outputs(outputs)
        if stale:
            print("Arquivos gerados estao desatualizados em relacao a core/manifest/manifest.yaml:\n", file=sys.stderr)
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
