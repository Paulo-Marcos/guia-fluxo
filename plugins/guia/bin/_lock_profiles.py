"""Perfis de travas (D-158 no `init`, D-161 no `configure`).

Um perfil e so um template de `.guia/locks/registry.yaml`. O perfil de um
registry existente se reconhece pelos ids das travas: o mesmo conjunto de um
template e aquele perfil; qualquer outro conjunto e `personalizado` - travas
proprias do projeto, que trocar de perfil apagaria.
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

LOCK_PROFILES: dict[str, str] = {
    "adicoes": "locks/registry.yaml",
    "testes": "locks/registry.testes.yaml",
    "nenhum": "locks/registry.nenhum.yaml",
}
DEFAULT_LOCK_PROFILE = "adicoes"
PROFILE_NO_LOCKS = "nenhum"
PROFILE_CUSTOM = "personalizado"


def _ids(registry: Path) -> set[str]:
    import yaml  # tardio: so quem le registry precisa do pyyaml

    data = yaml.safe_load(registry.read_text(encoding="utf-8")) or {}
    return {str(lock.get("id")) for lock in data.get("locks") or []}


def detect_profile(registry: Path, templates_dir: Path | None) -> str | None:
    """Perfil do registry: None sem arquivo; `personalizado` se nao bate ou nao da para ler."""
    if not registry.is_file():
        return None
    if templates_dir is None:
        return PROFILE_CUSTOM
    try:
        current = _ids(registry)
        for profile, template in LOCK_PROFILES.items():
            if (templates_dir / template).is_file() and _ids(templates_dir / template) == current:
                return profile
    except Exception:  # registry ilegivel: personalizado, o lado que nao sobrescreve as cegas
        pass
    return PROFILE_CUSTOM


def write_profile(profile: str, templates_dir: Path | None, registry: Path, backup_dir: Path) -> Path | None:
    """Troca o registry pelo template do perfil; o anterior vai para `backup_dir`."""
    template = templates_dir / LOCK_PROFILES[profile] if templates_dir else None
    if template is None or not template.is_file():
        raise SystemExit(f"Template do perfil {profile!r} nao encontrado: reinstale o plugin.")
    backup = None
    if registry.is_file():
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / f"registry.yaml.{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        shutil.copy2(registry, backup)
    registry.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(template, registry)
    return backup


__all__ = [
    "DEFAULT_LOCK_PROFILE", "LOCK_PROFILES", "PROFILE_CUSTOM", "PROFILE_NO_LOCKS",
    "detect_profile", "write_profile",
]
