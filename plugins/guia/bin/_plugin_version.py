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


def _obj(value: Any) -> dict[str, Any]:
    # Formato que o Claude Code mudar (ou arquivo corrompido) vira silencio, nao traceback.
    return value if isinstance(value, dict) else {}


def _read(path: Path) -> dict[str, Any]:
    try:
        return _obj(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return {}


def _version_key(version: str) -> tuple[int, ...] | None:
    try:
        return tuple(int(part) for part in version.strip().split("."))
    except ValueError:
        return None


def _available(market: dict[str, Any]) -> str | None:
    """A versao do plugin no marketplace: o `plugin.json` da fonte, ou a do catalogo."""
    location = market.get("installLocation") or _obj(market.get("source")).get("path")
    if not isinstance(location, str) or not location:
        return None
    root = Path(location)
    plugins = _read(root / ".claude-plugin" / "marketplace.json").get("plugins")
    entries = [_obj(p) for p in plugins] if isinstance(plugins, list) else []
    entry = next((p for p in entries if p.get("name") == PLUGIN_NAME), None)
    if entry is None:
        return None
    source = entry.get("source")
    if isinstance(source, str):
        version = _read(root / source / ".claude-plugin" / "plugin.json").get("version")
        if version:
            return str(version)
    return str(entry["version"]) if entry.get("version") else None


def stale_plugin_lines() -> list[str]:
    """Uma linha por instalacao do `guia` atras da versao que o marketplace ja tem."""
    plugins_dir = _claude_dir() / "plugins"
    installed = _obj(_read(plugins_dir / "installed_plugins.json").get("plugins"))
    markets = _read(plugins_dir / "known_marketplaces.json")
    lines = []
    for key, installs in installed.items():
        name, _, market_name = key.partition("@")
        if name != PLUGIN_NAME or not isinstance(installs, list):
            continue
        available = _available(_obj(markets.get(market_name)))
        for install in installs:
            current = str(_obj(install).get("version") or "")
            have, want = _version_key(current), _version_key(available or "")
            if have is not None and want is not None and have < want:
                lines.append(f"{STALE_PREFIX}{key} {current} instalado, {available} disponivel - os commands "
                             f"rodam o texto antigo; atualize com /plugin update {key} e reabra o chat")
    return lines


def print_stale_plugin() -> None:
    for line in stale_plugin_lines():
        print(line)


__all__ = ["print_stale_plugin", "stale_plugin_lines"]
