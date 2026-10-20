"""CLI handler: dashboard - painel local dos projetos e da fila (D-175).

Sem flags, registra o projeto atual (quando tem `.guia/`) e sobe um servidor
HTTP so em 127.0.0.1 que serve a pagina e `/api/snapshot`. O painel nunca
grava estado: as duas acoes (D-187, `POST /api/action/queue-resume|queue-run`)
rodam o motor dentro do projeto. Pedido de escrita so passa com Host local,
Origin do proprio painel, corpo JSON e o token desta sessao do painel, que
vai embutido na pagina - outra origem nao le a pagina, entao nao tem o token.
"""

from __future__ import annotations

import argparse
import hmac
import json
import secrets
import socket
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from _constants import ROOT
from _dashboard import add_projects, is_project, load_projects, overview, registry_file, remove_project, scan
from _dashboard_actions import ACTIONS, ActionError, registered_project
from _dashboard_page import PAGE_HTML, TOKEN_PLACEHOLDER

DEFAULT_PORT = 8765
_PORT_TRIES = 10
_MAX_BODY = 4096
_ACTION_PREFIX = "/api/action/"
TOKEN_HEADER = "X-Guia-Token"


def _handler(port_ref: list[int], token: str) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, body: bytes, content_type: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            # Os botoes (D-187) nao podem ser clicados por baixo de outra pagina.
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, code: int, payload: dict[str, object]) -> None:
            self._send(code, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

        def _local_names(self) -> set[str]:
            return {f"127.0.0.1:{port_ref[0]}", f"localhost:{port_ref[0]}"}

        def _host_ok(self) -> bool:
            # Contra DNS rebinding: so responde a quem chamou pelo endereco local.
            return (self.headers.get("Host") or "").lower() in self._local_names()

        def do_GET(self) -> None:  # noqa: N802 - nome da API do http.server
            if not self._host_ok():
                self._send(403, b"host nao permitido", "text/plain; charset=utf-8")
                return
            path = self.path.split("?", 1)[0]
            if path == "/":
                page = PAGE_HTML.replace(TOKEN_PLACEHOLDER, token)
                self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
            elif path == "/api/snapshot":
                body = json.dumps(overview(load_projects()), ensure_ascii=False).encode("utf-8")
                self._send(200, body, "application/json; charset=utf-8")
            else:
                self._send(404, b"nao encontrado", "text/plain; charset=utf-8")

        def _refusal(self) -> tuple[int, str] | None:
            """Por que o pedido de escrita nao passa, ou None. Cada portao
            fecha uma via: Host (rebinding), Origin (pagina de outra origem),
            JSON (formulario simples, que dispensa preflight) e token
            (quem nao carregou a pagina do painel)."""
            if not self._host_ok():
                return 403, "host nao permitido"
            origin = (self.headers.get("Origin") or "").lower()
            if origin not in {f"http://{name}" for name in self._local_names()}:
                return 403, "origem nao permitida"
            content_type = (self.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
            if content_type != "application/json":
                return 415, "corpo precisa ser application/json"
            sent = (self.headers.get(TOKEN_HEADER) or "").encode("utf-8")
            if not hmac.compare_digest(sent, token.encode("utf-8")):
                return 403, "token do painel ausente ou invalido (recarregue a pagina)"
            return None

        def _read_body(self) -> bytes | None:
            """Le o corpo antes de qualquer resposta: recusar com bytes nao
            lidos no socket faz o Windows mandar RST e o cliente nao ve o 403."""
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = -1
            if not 0 < length <= _MAX_BODY:
                self.close_connection = True
                return None
            return self.rfile.read(length)

        def do_POST(self) -> None:  # noqa: N802 - nome da API do http.server
            raw = self._read_body()
            refusal = self._refusal()
            if refusal:
                self._send_json(refusal[0], {"ok": False, "message": refusal[1]})
                return
            path = self.path.split("?", 1)[0]
            action = ACTIONS.get(path[len(_ACTION_PREFIX):]) if path.startswith(_ACTION_PREFIX) else None
            if action is None:
                self._send_json(404, {"ok": False, "message": "acao desconhecida"})
                return
            if raw is None:
                self._send_json(400, {"ok": False, "message": "corpo ausente ou grande demais"})
                return
            try:
                body = json.loads(raw.decode("utf-8"))
                root = registered_project(body.get("project") if isinstance(body, dict) else None)
                message = action(root)
            except ValueError:
                self._send_json(400, {"ok": False, "message": "corpo nao e JSON valido"})
                return
            except ActionError as exc:
                self._send_json(exc.status, {"ok": False, "message": str(exc)})
                return
            except Exception as exc:  # noqa: BLE001 - o painel responde, nao cai
                self._send_json(500, {"ok": False, "message": f"{type(exc).__name__}: {exc}"})
                return
            self._send_json(200, {"ok": True, "message": message})

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            return  # o terminal fica limpo; o painel faz polling a cada poucos segundos

    return Handler


class _ExclusiveServer(ThreadingHTTPServer):
    """Porta so nossa. O HTTPServer liga SO_REUSEADDR, que no Windows deixa um
    segundo processo ocupar a mesma porta: dois paineis dividiriam a porta e a
    busca pela proxima livre nunca andaria."""

    allow_reuse_address = False

    def server_bind(self) -> None:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def _bind(port: int) -> ThreadingHTTPServer:
    """Sobe o servidor; `guia_token` e o token desta sessao do painel (D-187)."""
    port_ref = [port]
    token = secrets.token_urlsafe(32)
    last_error: OSError | None = None
    for candidate in range(port, port + _PORT_TRIES):
        port_ref[0] = candidate
        try:
            server = _ExclusiveServer(("127.0.0.1", candidate), _handler(port_ref, token))
            server.guia_token = token  # type: ignore[attr-defined]
            return server
        except OSError as exc:
            last_error = exc
    raise SystemExit(f"Nenhuma porta livre entre {port} e {port + _PORT_TRIES - 1}: {last_error}")


def _serve(args: argparse.Namespace) -> int:
    server = _bind(args.port)
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"PAINEL: {url}")
    print(f"Projetos: {len(load_projects())} (cadastro em {registry_file()}). Ctrl+C encerra.")
    if not args.no_open:
        threading.Timer(0.4, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nPainel encerrado.")
    finally:
        server.server_close()
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    changed = False
    for raw in args.add:
        path = Path(raw)
        if not is_project(path):
            raise SystemExit(f"{path} nao tem .guia/tasks.json: nao e um projeto do Guia.")
        added = add_projects([path])
        print(f"Cadastrado: {added[0]}" if added else f"Ja cadastrado: {path.resolve()}")
        changed = True
    for raw in args.remove:
        print(f"Removido: {raw}" if remove_project(Path(raw)) else f"Nao estava cadastrado: {raw}")
        changed = True
    for raw in args.scan:
        found = scan(Path(raw), depth=args.depth)
        added = add_projects(found)
        print(f"{raw}: {len(found)} projeto(s) encontrado(s), {len(added)} novo(s).")
        for path in added:
            print(f"  + {path}")
        changed = True
    if is_project(ROOT):
        add_projects([ROOT])
    if args.list:
        for path in load_projects():
            print(path)
        return 0
    if args.json:
        print(json.dumps(overview(load_projects()), ensure_ascii=False, indent=2))
        return 0
    if changed and not args.serve:
        return 0
    return _serve(args)


def add_dashboard_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser(
        "dashboard",
        help="Painel local (D-175): projetos da maquina, demandas por etapa e a fila de integracao, no navegador. Le o estado; os botoes da fila (D-187) rodam o motor no projeto.",
    )
    p.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Porta local (padrao {DEFAULT_PORT}; tenta as seguintes se ocupada).")
    p.add_argument("--no-open", action="store_true", help="Nao abre o navegador.")
    p.add_argument("--add", action="append", default=[], metavar="PASTA", help="Cadastra um projeto. Repetivel.")
    p.add_argument("--remove", action="append", default=[], metavar="PASTA", help="Tira um projeto do cadastro. Repetivel.")
    p.add_argument("--scan", action="append", default=[], metavar="PASTA", help="Procura projetos do Guia sob a pasta e cadastra. Repetivel.")
    p.add_argument("--depth", type=int, default=3, help="Profundidade do --scan (padrao 3).")
    p.add_argument("--list", action="store_true", help="Lista os projetos cadastrados e sai.")
    p.add_argument("--json", action="store_true", help="Imprime o retrato de todos os projetos em JSON e sai.")
    p.add_argument("--serve", action="store_true", help="Com --add/--remove/--scan, sobe o painel em seguida.")
    p.set_defaults(func=cmd_dashboard)


__all__ = ["add_dashboard_parser", "cmd_dashboard"]
