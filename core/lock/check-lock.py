#!/usr/bin/env python3
"""check-lock.py - Thin CLI wrapper over `lock_api`.

Behavior identical to the previous monolithic version, but every piece of
logic now lives in `lock_api` (see that module's docstring). This file is
the user-facing shell: argparse, formatting, exit codes, hook integration.

Uso:
    python core/lock/check-lock.py list                                       [--json]
    python core/lock/check-lock.py check [--operation X] <arquivo>...         [--json]
    python core/lock/check-lock.py info <feature-id>                          [--json]
    python core/lock/check-lock.py lock <feature-id> --description "..." [--operations ...] [--allow-missing] <arquivo>...
    python core/lock/check-lock.py edit <feature-id> [--add-file F]... [--remove-file F]... [--description "..."] [--allow-missing]
    python core/lock/check-lock.py unlock <feature-id>
    python core/lock/check-lock.py audit                                      [--json]
    python core/lock/check-lock.py history <feature-id>                       [--json]
    python core/lock/check-lock.py hook <commit-msg-file>                     # git hook
    python core/lock/check-lock.py ci --files F --messages M                  # CI

Veja features/README.md para o protocolo completo.

Requer Python 3.10+ e PyYAML.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

# lock_api is a sibling module; ensure this folder is on sys.path when
# invoked as a standalone script.
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import lock_api  # noqa: E402


# -- Printing ---------------------------------------------------------------


def print_block(blocked: list[lock_api.LockMatch], stream) -> None:
    print("Arquivos travados em features/registry.yaml:\n", file=stream)
    for match in blocked:
        desc = match.lock.get("description") or "sem descricao"
        print(f"  - {match.path}", file=stream)
        print(f"    operacao: {match.operation}", file=stream)
        print(f"    feature: {match.lock['id']}", file=stream)
        print(f"    protege: {desc}", file=stream)
    ids = sorted({match.lock["id"] for match in blocked})
    print(
        "\nAntes de pedir unlock, explique impacto esperado, risco de regressao e alternativas.",
        file=stream,
    )
    print(
        "Para desbloquear, peca autorizacao ao dono e inclua na mensagem do commit:",
        file=stream,
    )
    for fid in ids:
        print(f"  [unlock:{fid}] motivo: <razao>", file=stream)


# -- Subcommands ------------------------------------------------------------


def _print_json(payload) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def cmd_list(args: argparse.Namespace) -> int:
    locks = lock_api.load_locks()
    if args.json:
        _print_json({"count": len(locks), "locks": locks})
        return 0
    if not locks:
        print("Nenhuma trava ativa.")
        return 0
    print(f"{len(locks)} feature(s) travada(s):\n")
    for lock in locks:
        desc = lock.get("description", "")
        operations = ", ".join(sorted(lock_api.lock_operations(lock)))
        suffix = f" - {desc}" if desc else ""
        print(f"* {lock['id']} [{operations}]{suffix}")
        for f in lock.get("files", []) or []:
            print(f"    {f}")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    events = lock_api.events_from_paths(args.files, args.operation)
    blocked = lock_api.find_blocked(events)
    if args.json:
        _print_json({
            "ok": not blocked,
            "checked": len(args.files),
            "blocked": [
                {"path": m.path, "operation": m.operation, "lockId": m.lock["id"]}
                for m in blocked
            ],
        })
        return 0 if not blocked else 1
    if not blocked:
        print(f"OK: {len(args.files)} arquivo(s), nenhum travado.")
        return 0
    print_block(blocked, sys.stderr)
    return 1


def cmd_info(args: argparse.Namespace) -> int:
    lock = lock_api.get_lock(args.id)
    if lock is None:
        if args.json:
            _print_json({"found": False, "id": args.id})
        else:
            print(f"Lock nao encontrado: {args.id}", file=sys.stderr)
        return 1
    if args.json:
        _print_json(lock)
        return 0
    print(f"id:          {lock['id']}")
    if lock.get("description"):
        print(f"description: {lock['description']}")
    if lock.get("locked_at"):
        print(f"locked_at:   {lock['locked_at']}")
    operations = ", ".join(sorted(lock_api.lock_operations(lock)))
    print(f"operations:  {operations}")
    files = lock.get("files", []) or []
    print(f"files ({len(files)}):")
    for f in files:
        print(f"  - {f}")
    return 0


def cmd_edit(args: argparse.Namespace) -> int:
    try:
        updated = lock_api.edit_lock(
            args.id,
            add_files=args.add_file or [],
            remove_files=args.remove_file or [],
            description=args.description,
            allow_missing=args.allow_missing,
        )
    except lock_api.LockNotFound:
        print(f"Erro: lock '{args.id}' nao encontrado.", file=sys.stderr)
        return 1
    except lock_api.LockIgnoredPath as exc:
        print(
            f"Erro: arquivo nao pode ser travado (esta em lock-ignore.txt): {exc.args[0]}",
            file=sys.stderr,
        )
        return 1
    except lock_api.LockOutsideRepo as exc:
        print(f"Erro: path traversal recusado (fora do repo): {exc.args[0]}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    if args.json:
        _print_json(updated)
    else:
        print(f"Lock '{args.id}' atualizado. {len(updated.get('files', []))} arquivo(s).")
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    """Lista commits que tocaram este lock id via [unlock:<id>] no message."""
    if not (lock_api.REPO_ROOT / ".git").exists():
        print(
            "Erro: nao parece um repositorio git (sem .git/). history precisa de git log.",
            file=sys.stderr,
        )
        return 1
    pattern = f"[unlock:{args.id}]"
    try:
        log = subprocess.check_output(
            [
                "git",
                "-c",
                f"safe.directory={lock_api.REPO_ROOT.as_posix()}",
                "log",
                "--fixed-strings",
                "--grep",
                pattern,
                "--pretty=format:%h|%ad|%s",
                "--date=short",
            ],
            text=True,
            cwd=lock_api.REPO_ROOT,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"Erro ao consultar git log: {exc}", file=sys.stderr)
        return 1
    entries = []
    for line in log.strip().splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3:
            entries.append({"sha": parts[0], "date": parts[1], "subject": parts[2]})
    if args.json:
        _print_json({"id": args.id, "count": len(entries), "history": entries})
        return 0
    if not entries:
        print(f"Nenhum unlock registrado para '{args.id}' no historico.")
        return 0
    print(f"{len(entries)} unlock(s) de '{args.id}' no historico:\n")
    for entry in entries:
        print(f"  {entry['date']}  {entry['sha']}  {entry['subject']}")
    return 0


def cmd_lock(args: argparse.Namespace) -> int:
    spec = lock_api.LockSpec(
        id=args.id,
        description=args.description or "",
        operations=tuple(args.operations),
        files=tuple(args.files),
    )
    try:
        lock_api.add_lock(spec, locked_at=date.today().isoformat(), allow_missing=args.allow_missing)
    except lock_api.LockExists:
        print(f"Erro: feature '{args.id}' ja existe no registry.", file=sys.stderr)
        return 1
    except lock_api.LockIgnoredPath as exc:
        print(
            f"Erro: arquivo nao pode ser travado por features/lock-ignore.txt: {exc.args[0]}",
            file=sys.stderr,
        )
        return 1
    except lock_api.LockOutsideRepo as exc:
        print(
            f"Erro: path traversal recusado (fora do repo): {exc.args[0]}",
            file=sys.stderr,
        )
        return 1
    except FileNotFoundError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    print(f"Trava criada: {args.id}  ({len(args.files)} arquivo(s))")
    return 0


def cmd_unlock(args: argparse.Namespace) -> int:
    try:
        lock_api.remove_lock(args.id)
    except lock_api.LockNotFound:
        print(f"Erro: feature '{args.id}' nao encontrada no registry.", file=sys.stderr)
        return 1
    print(f"Trava removida: {args.id}")
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    if not (lock_api.REPO_ROOT / ".git").exists():
        print(
            "Erro: nao parece um repositorio git (sem .git/). audit precisa de git log.",
            file=sys.stderr,
        )
        return 1
    try:
        log = subprocess.check_output(
            [
                "git",
                "-c",
                f"safe.directory={lock_api.REPO_ROOT.as_posix()}",
                "log",
                "--fixed-strings",
                "--grep",
                "[unlock:",
                "--pretty=format:%h|%ad|%s",
                "--date=short",
            ],
            text=True,
            cwd=lock_api.REPO_ROOT,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"Erro ao consultar git log: {exc}", file=sys.stderr)
        return 1
    entries = []
    for line in log.strip().splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3:
            entries.append({"sha": parts[0], "date": parts[1], "subject": parts[2]})
    if args.json:
        _print_json({"count": len(entries), "unlocks": entries})
        return 0
    if not entries:
        print("Nenhum desbloqueio registrado no historico.")
        return 0
    print("Desbloqueios registrados:\n")
    for entry in entries:
        print(f"  {entry['date']}  {entry['sha']}  {entry['subject']}")
    return 0


def cmd_hook(args: argparse.Namespace) -> int:
    msg = Path(args.msg_file).read_text(encoding="utf-8")
    try:
        staged = subprocess.check_output(
            ["git", "diff", "--cached", "--name-status", "--diff-filter=ACMRD"],
            text=True,
            cwd=lock_api.REPO_ROOT,
        ).splitlines()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return 0

    events = lock_api.events_from_name_status(staged)
    blocked = lock_api.find_blocked(events)
    if not blocked:
        return 0
    still = lock_api.filter_unlocked(blocked, msg)
    if not still:
        return 0

    print("\nCOMMIT BLOQUEADO - features travadas:\n", file=sys.stderr)
    print_block(still, sys.stderr)
    print(
        "\nEdite a mensagem (git commit --amend) ou refaca o commit com as marcas acima.\n"
        "Lembre de incluir tambem `motivo: <razao curta>` no commit.",
        file=sys.stderr,
    )
    return 1


def cmd_ci(args: argparse.Namespace) -> int:
    lines = [
        line.strip()
        for line in Path(args.files).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    msg_path = Path(args.messages)
    msg = msg_path.read_text(encoding="utf-8") if msg_path.exists() else ""

    events = lock_api.events_from_name_status(lines)
    blocked = lock_api.find_blocked(events)
    if not blocked:
        print(f"OK: {len(events)} operacao(oes), nenhum travado.")
        return 0
    still = lock_api.filter_unlocked(blocked, msg)
    if not still:
        print("OK: arquivos travados foram desbloqueados via [unlock:...] nos commits.")
        return 0
    print(
        "\nFALHA - PR modifica arquivos travados sem [unlock:<feature-id>] + motivo:\n",
        file=sys.stderr,
    )
    print_block(still, sys.stderr)
    return 1


# -- Entry point ------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validador e gerenciador de travas de edicao.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="Lista travas ativas")
    p_list.add_argument("--json", action="store_true", help="Saida em JSON.")
    p_list.set_defaults(func=cmd_list)

    p_check = sub.add_parser("check", help="Checa arquivos pontuais")
    p_check.add_argument(
        "--operation",
        choices=lock_api.ALL_OPERATIONS,
        help="Operacao a checar; default: modify se existe, add se nao existe",
    )
    p_check.add_argument("--json", action="store_true", help="Saida em JSON.")
    p_check.add_argument("files", nargs="+")
    p_check.set_defaults(func=cmd_check)

    p_info = sub.add_parser("info", help="Mostra detalhes de uma trava por id")
    p_info.add_argument("id", help="Identificador da trava")
    p_info.add_argument("--json", action="store_true", help="Saida em JSON.")
    p_info.set_defaults(func=cmd_info)

    p_edit = sub.add_parser("edit", help="Edita uma trava existente (add/remove file, description).")
    p_edit.add_argument("id", help="Identificador da trava")
    p_edit.add_argument("--add-file", action="append", default=[], help="Adicionar arquivo (repetir).")
    p_edit.add_argument("--remove-file", action="append", default=[], help="Remover arquivo (repetir).")
    p_edit.add_argument("--description", help="Nova descricao (substitui).")
    p_edit.add_argument(
        "--allow-missing",
        action="store_true",
        help="Aceita arquivos inexistentes em --add-file.",
    )
    p_edit.add_argument("--json", action="store_true", help="Saida em JSON.")
    p_edit.set_defaults(func=cmd_edit)

    p_lock = sub.add_parser("lock", help="Adiciona trava a uma feature")
    p_lock.add_argument("id", help="Identificador da feature (kebab-case)")
    p_lock.add_argument("--description", "-d", default="", help="Descricao curta")
    p_lock.add_argument(
        "--operations",
        nargs="+",
        choices=lock_api.ALL_OPERATIONS,
        default=list(lock_api.ALL_OPERATIONS),
        help="Operacoes bloqueadas",
    )
    p_lock.add_argument(
        "--allow-missing",
        action="store_true",
        help="Aceita arquivos inexistentes (uso valido: travar criacao futura).",
    )
    p_lock.add_argument("files", nargs="+", help="Arquivos a travar (paths relativos ao repo)")
    p_lock.set_defaults(func=cmd_lock)

    p_unlock = sub.add_parser("unlock", help="Remove trava de uma feature (permanente)")
    p_unlock.add_argument("id", help="Identificador da feature")
    p_unlock.set_defaults(func=cmd_unlock)

    p_audit = sub.add_parser("audit", help="Lista desbloqueios temporarios no git log")
    p_audit.add_argument("--json", action="store_true", help="Saida em JSON.")
    p_audit.set_defaults(func=cmd_audit)

    p_history = sub.add_parser("history", help="Lista commits que liberaram uma trava por id")
    p_history.add_argument("id", help="Identificador da trava")
    p_history.add_argument("--json", action="store_true", help="Saida em JSON.")
    p_history.set_defaults(func=cmd_history)

    p_hook = sub.add_parser("hook", help="Modo git commit-msg")
    p_hook.add_argument("msg_file")
    p_hook.set_defaults(func=cmd_hook)

    p_ci = sub.add_parser("ci", help="Modo CI (le arquivos+mensagens de arquivos)")
    p_ci.add_argument("--files", required=True)
    p_ci.add_argument("--messages", required=True)
    p_ci.set_defaults(func=cmd_ci)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
