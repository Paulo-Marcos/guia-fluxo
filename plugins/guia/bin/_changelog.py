"""CHANGELOG por fragmentos (D-121, R9).

Cada demanda escreve `<dir>/<ID>.<categoria>.md` (padrao `changelog.d/`):
o fragmento e versionado e viaja no PR, entao dois PRs nunca editam a mesma
linha do CHANGELOG. `compile` junta os fragmentos no `[Unreleased]` - ou fecha
uma versao -, agrupados na ordem do Keep a Changelog e por id numerico,
preservando o que ja estava escrito, e apaga os fragmentos.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from _git_ops import git_output

CHANGELOG_DIR_DEFAULT = "changelog.d"
CHANGELOG_FILE_DEFAULT = "CHANGELOG.md"
CATEGORY_ORDER = ("Added", "Changed", "Deprecated", "Removed", "Fixed", "Security")
CATEGORY_BY_KIND_DEFAULT = {
    "feature": "Added",
    "bug": "Fixed",
    "issue": "Fixed",
    "chore": "Changed",
    "epic": "Changed",
}
UNRELEASED_HEADING = "## [Unreleased]"
_FRAGMENT_RE = re.compile(r"^([A-Za-z]+)-(\d+)\.([A-Za-z]+)\.md$")


def changelog_settings(config: dict[str, Any]) -> dict[str, Any]:
    changelog = (config.get("delivery") or {}).get("changelog") or {}
    return {
        "style": changelog.get("style") or "inline",
        "dir": changelog.get("dir") or CHANGELOG_DIR_DEFAULT,
        "file": changelog.get("file") or CHANGELOG_FILE_DEFAULT,
        "categoryByKind": {**CATEGORY_BY_KIND_DEFAULT, **(changelog.get("categoryByKind") or {})},
    }


def work_root(cwd: Path | None = None) -> Path:
    """Raiz da arvore de trabalho (o worktree da demanda, nao a principal)."""
    cwd = cwd or Path.cwd()
    toplevel = git_output(cwd, "rev-parse", "--show-toplevel")
    return Path(toplevel) if toplevel else cwd


def _category_name(raw: str) -> str:
    return next((name for name in CATEGORY_ORDER if name.lower() == raw.lower()), raw.capitalize())


def add_fragment(root: Path, settings: dict[str, Any], task: dict[str, Any], category: str | None, text: str | None) -> Path:
    category = _category_name(category or settings["categoryByKind"].get(task.get("kind", ""), "Changed"))
    path = root / settings["dir"] / f"{task['id']}.{category.lower()}.md"
    if path.exists():
        raise SystemExit(f"{path.relative_to(root).as_posix()} ja existe: edite o fragmento em vez de recriar.")
    body = (text or f"{task['title']} ({task['id']})").strip()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text((body if body.startswith("- ") else f"- {body}") + "\n", encoding="utf-8", newline="\n")
    return path


def _fragments(folder: Path) -> list[tuple[tuple[str, int], str, str, Path]]:
    found = []
    for path in folder.glob("*.md") if folder.is_dir() else []:
        match = _FRAGMENT_RE.match(path.name)
        if match:
            key = (match.group(1).upper(), int(match.group(2)))
            body = path.read_text(encoding="utf-8").strip()
            found.append((key, _category_name(match.group(3)), body, path))
    return sorted(found, key=lambda item: item[0])


def _split_unreleased(text: str) -> tuple[str, str, str]:
    """(antes do [Unreleased], corpo dele, o resto a partir da proxima versao)."""
    start = text.index(UNRELEASED_HEADING)
    body_start = start + len(UNRELEASED_HEADING)
    following = text.find("\n## [", body_start)
    end = following + 1 if following != -1 else len(text)
    return text[:start], text[body_start:end], text[end:]


def _parse_categories(body: str) -> tuple[list[str], dict[str, list[str]]]:
    order: list[str] = []
    sections: dict[str, list[str]] = {}
    current = None
    for line in body.splitlines():
        if line.startswith("### "):
            current = line[4:].strip()
            order.append(current)
            sections.setdefault(current, [])
        elif current is not None and line.strip():
            sections[current].append(line)
    return order, sections


def compile_fragments(root: Path, settings: dict[str, Any], version: str | None = None, date: str | None = None) -> list[Path]:
    """Junta os fragmentos no CHANGELOG; devolve os fragmentos consumidos."""
    fragments = _fragments(root / settings["dir"])
    changelog = root / settings["file"]
    text = changelog.read_text(encoding="utf-8")
    if not fragments and version is None:
        return []
    if UNRELEASED_HEADING not in text:
        raise SystemExit(f"{settings['file']} sem a secao {UNRELEASED_HEADING}.")
    before, body, rest = _split_unreleased(text)
    order, sections = _parse_categories(body)
    for _key, category, fragment, _path in fragments:
        if category not in sections:
            sections[category] = []
            order.append(category)
        sections[category].extend(fragment.splitlines())
    ordered = [c for c in CATEGORY_ORDER if c in sections] + [c for c in order if c not in CATEGORY_ORDER]
    blocks = "\n\n".join(f"### {c}\n" + "\n".join(sections[c]) for c in ordered if sections[c])
    if version is None:
        section = UNRELEASED_HEADING + ("\n\n" + blocks if blocks else "") + "\n\n"
    else:
        heading = f"## [{version}]" + (f" - {date}" if date else "")
        section = f"{UNRELEASED_HEADING}\n\n{heading}" + ("\n\n" + blocks if blocks else "") + "\n\n"
    changelog.write_text(before + section + rest, encoding="utf-8", newline="\n")
    for *_ignored, path in fragments:
        path.unlink()
    return [path for *_ignored, path in fragments]


__all__ = [
    "CATEGORY_ORDER",
    "add_fragment",
    "changelog_settings",
    "compile_fragments",
    "work_root",
]
