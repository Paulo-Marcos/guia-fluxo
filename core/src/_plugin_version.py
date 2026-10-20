"""Plugin instalado atras do marketplace (D-190).

No gerador-cortes o `installed_plugins.json` do Claude Code seguia no 0.9.0,
anterior a D-185/D-188, e os chats rodavam o texto velho dos commands - sem
renomear nem gravar a sessao. O motor so le os arquivos do Claude Code e avisa;
atualizar e do dono (`/plugin update`). Qualquer arquivo ausente ou ilegivel
vira silencio: o aviso e um empurrao, nunca um erro.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

PLUGIN_NAME = "guia"
STALE_PREFIX = "PLUGIN DESATUALIZADO: "


def _claude_dir() -> Path:
    # CLAUDE_CONFIG_DIR e o mesmo override que o Claude Code respeita.
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def _read(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _version_key(version: str) -> tuple[int, ...] | None:
    try:
        return tuple(int(part) for part in version.strip().split("."))
    except (AttributeError, ValueError):
        return None


def _available(market: dict[str, Any]) -> str | None:
    """A versao do plugin no marketplace: o `plugin.json` da fonte, ou a do catalogo."""
    location = market.get("installLocation") or (market.get("source") or {}).get("path")
    if not location:
        return None
    root = Path(location)
    catalog = _read(root / ".claude-plugin" / "marketplace.json") or {}
    entry = next((p for p in catalog.get("plugins") or [] if p.get("name") == PLUGIN_NAME), None)
    if entry is None:
        return None
    source = entry.get("source")
    if isinstance(source, str):
        manifest = _read(root / source / ".claude-plugin" / "plugin.json") or {}
        if manifest.get("version"):
            return str(manifest["version"])
    return entry.get("version")


def stale_plugin_lines() -> list[str]:
    """Uma linha por instalacao do `guia` atras da versao que o marketplace ja tem."""
    plugins_dir = _claude_dir() / "plugins"
    installed = (_read(plugins_dir / "installed_plugins.json") or {}).get("plugins") or {}
    markets = _read(plugins_dir / "known_marketplaces.json") or {}
    lines = []
    for key, installs in installed.items():
        name, _, market_name = key.partition("@")
        if name != PLUGIN_NAME or not isinstance(installs, list):
            continue
        available = _available(markets.get(market_name) or {})
        for install in installs:
            current = str(install.get("version") or "")
            have, want = _version_key(current), _version_key(available or "")
            if have is not None and want is not None and have < want:
                lines.append(f"{STALE_PREFIX}{key} {current} instalado, {available} disponivel - os commands "
                             f"rodam o texto antigo; atualize com /plugin update {key} e reabra o chat")
    return lines


def print_stale_plugin() -> None:
    for line in stale_plugin_lines():
        print(line)


__all__ = ["print_stale_plugin", "stale_plugin_lines"]
