"""CLI handler: painel - o atalho do dono para o painel e a fila (D-203).

O dono abria um chat de IA so para ver o painel ou ligar a fila. `painel`
faz as duas coisas sem sessao de IA, num comando curto ou num atalho do
Windows (`--atalho`):

1. liga o executor da fila do projeto atual pelo mesmo `start_executor` do
   botao do painel (D-187) - executor vivo, fila parada ou projeto sem PR so
   viram aviso, nunca um segundo executor;
2. abre o painel: reaproveita um painel ja aberto nesta maquina (o atalho
   clicado duas vezes nao sobe dois servidores), senao sobe um.

Quem dispara e o dono (terminal ou atalho), como o clique do D-187: nao fere
o D-098. Por isso nao ha command de plugin para este verbo.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

from _cli_dashboard import _PORT_TRIES, DEFAULT_PORT, _serve
from _constants import ROOT
from _dashboard import PROJECT_ENGINES, add_projects, engine_for, is_project
from _dashboard_actions import ActionError, start_executor

_PROBE_TIMEOUT_SECONDS = 1.0
_SHORTCUT_SCRIPT = r"""
$shell = New-Object -ComObject WScript.Shell
foreach ($folder in @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs'))) {
    $link = $shell.CreateShortcut((Join-Path $folder $env:GUIA_LNK_NAME))
    $link.TargetPath = $env:GUIA_LNK_TARGET
    $link.Arguments = $env:GUIA_LNK_ARGS
    $link.WorkingDirectory = $env:GUIA_LNK_DIR
    $link.Description = 'Guia Fluxo: abre o painel e liga a fila'
    $link.Save()
    Write-Output $link.FullName
}
"""


def ensure_queue(root: Path) -> str:
    """Liga o executor; o que o painel recusaria vira aviso de uma linha."""
    try:
        return f"FILA: {start_executor(root)}"
    except ActionError as exc:
        return f"FILA: {exc}"


def running_dashboard(port: int) -> str | None:
    """URL de um painel do Guia ja escutando entre `port` e as seguintes."""
    for candidate in range(port, port + _PORT_TRIES):
        url = f"http://127.0.0.1:{candidate}/"
        try:
            with urllib.request.urlopen(f"{url}api/snapshot", timeout=_PROBE_TIMEOUT_SECONDS) as response:
                if isinstance(json.loads(response.read()), dict):
                    return url
        except (OSError, ValueError):
            continue
    return None


def create_shortcut(root: Path) -> list[str]:
    """Atalho na area de trabalho e no menu Iniciar que roda `painel` no projeto."""
    if os.name != "nt":
        raise SystemExit("--atalho cria atalho do Windows; fora dele use `guia painel` num alias do shell.")
    env = dict(os.environ)
    env.update({
        "GUIA_LNK_NAME": f"Guia - {root.name}.lnk",
        "GUIA_LNK_TARGET": sys.executable,
        "GUIA_LNK_ARGS": f'"{engine_for(root)}" painel',
        "GUIA_LNK_DIR": str(root),
    })
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", _SHORTCUT_SCRIPT],
        env=env, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        raise SystemExit(f"Atalho nao criado: {(result.stderr or result.stdout).strip()}")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def cmd_painel(args: argparse.Namespace) -> int:
    if not is_project(ROOT):
        raise SystemExit(f"{ROOT} nao tem .guia/tasks.json: rode `painel` na pasta de um projeto do Guia.")
    if args.atalho:
        for path in create_shortcut(ROOT):
            print(f"Atalho: {path}")
        if not any((ROOT / rel).is_file() for rel in PROJECT_ENGINES):
            print("O atalho aponta para o motor do plugin: depois de /plugin update, rode `painel --atalho` de novo.")
        return 0
    add_projects([ROOT])
    if not args.sem_fila:
        print(ensure_queue(ROOT))
    url = running_dashboard(args.port)
    if url is None:
        return _serve(args)
    print(f"PAINEL: {url} (ja aberto)")
    if not args.no_open:
        webbrowser.open(url)
    return 0


def add_painel_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser(
        "painel",
        help="Atalho do dono (D-203): liga o executor da fila do projeto e abre o painel, sem sessao de IA.",
    )
    p.add_argument("--sem-fila", action="store_true", help="So abre o painel, sem ligar o executor.")
    p.add_argument("--atalho", action="store_true",
                   help="Cria o atalho do Windows (area de trabalho e menu Iniciar) que roda `painel` neste projeto.")
    p.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Porta do painel (padrao {DEFAULT_PORT}).")
    p.add_argument("--no-open", action="store_true", help="Nao abre o navegador.")
    p.set_defaults(func=cmd_painel)


__all__ = ["add_painel_parser", "cmd_painel", "create_shortcut", "ensure_queue", "running_dashboard"]
