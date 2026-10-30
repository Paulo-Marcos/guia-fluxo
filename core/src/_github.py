"""Adaptador fino do GitHub (D-117, R2).

Unico lugar do motor que fala com o GitHub, via `gh` (sem token proprio,
sem dependencia nova). So leitura. Nos testes, `GUIA_GH_FIXTURE` aponta um
JSON com as respostas: chave = endpoint do `gh api`, valor = resposta; a
chave `__auth__` responde ao `gh auth status`. Endpoint ausente no fixture =
404. Mesmo espirito do `GUIA_NOW` (seam explicito, nunca ligado por padrao).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, NamedTuple

FIXTURE_ENV = "GUIA_GH_FIXTURE"
_REMOTE_RE = re.compile(r"github\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?/?$")


def _fixture() -> dict[str, Any] | None:
    path = os.environ.get(FIXTURE_ENV)
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def repo_slug(cwd: Path) -> str | None:
    """`dono/repo` do remoto `origin`, quando ele e do GitHub."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"], cwd=cwd, text=True, capture_output=True
        )
    except (FileNotFoundError, OSError):
        return None
    match = _REMOTE_RE.search(result.stdout.strip()) if result.returncode == 0 else None
    return f"{match.group(1)}/{match.group(2)}" if match else None


def gh_status() -> str:
    """`autenticado`, `nao autenticado` ou `gh ausente`."""
    fixture = _fixture()
    if fixture is not None:
        return "autenticado" if fixture.get("__auth__") else "nao autenticado"
    if shutil.which("gh") is None:
        return "gh ausente"
    result = subprocess.run(["gh", "auth", "status"], text=True, capture_output=True)
    return "autenticado" if result.returncode == 0 else "nao autenticado"


def gh_api(endpoint: str) -> tuple[Any | None, str | None]:
    """(resposta, erro) de `gh api <endpoint>`. 404 vira (None, "nao encontrado")."""
    fixture = _fixture()
    if fixture is not None:
        if endpoint in fixture:
            return fixture[endpoint], None
        return None, "nao encontrado"
    if shutil.which("gh") is None:
        return None, "gh ausente"
    result = subprocess.run(["gh", "api", endpoint], text=True, encoding="utf-8", capture_output=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        return None, "nao encontrado" if "404" in detail else (detail.splitlines() or ["erro"])[0]
    try:
        return json.loads(result.stdout), None
    except ValueError:
        return None, "resposta nao e JSON"


def _fixture_prs_path() -> Path | None:
    path = os.environ.get(FIXTURE_ENV)
    return Path(path + ".prs.json") if path else None


def _fixture_prs() -> list[dict[str, Any]]:
    path = _fixture_prs_path()
    return json.loads(path.read_text(encoding="utf-8")) if path and path.exists() else []


def gh_pr_find(cwd: Path, branch: str) -> dict[str, Any] | None:
    """PR aberto da `branch` ({number, url}) ou None."""
    if _fixture() is not None:
        return next((pr for pr in _fixture_prs() if pr.get("headRef") == branch), None)
    result = subprocess.run(
        ["gh", "pr", "view", branch, "--json", "number,url,state"],
        cwd=cwd, text=True, encoding="utf-8", capture_output=True,
    )
    if result.returncode != 0:
        return None
    data = json.loads(result.stdout)
    return data if data.get("state") == "OPEN" else None


def gh_pr_upsert(cwd: Path, base: str, branch: str, title: str, body: str) -> dict[str, Any]:
    """Abre o PR da `branch` ou atualiza titulo e corpo do que ja existe.

    Escrita no GitHub so por aqui. Corpo vai por arquivo (`--body-file`):
    nunca por argumento interpolado.
    """
    existing = gh_pr_find(cwd, branch)
    if _fixture() is not None:
        prs = _fixture_prs()
        if existing:
            for pr in prs:
                if pr["number"] == existing["number"]:
                    pr.update(title=title, body=body)
            result = existing
        else:
            result = {"number": len(prs) + 1, "url": f"https://example.invalid/pull/{len(prs) + 1}"}
            prs.append({**result, "headRef": branch, "base": base, "title": title, "body": body})
        _fixture_prs_path().write_text(json.dumps(prs, ensure_ascii=False), encoding="utf-8")
        return {"number": result["number"], "url": result["url"]}
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as handle:
        handle.write(body)
        body_file = handle.name
    try:
        if existing:
            command = ["gh", "pr", "edit", str(existing["number"]), "--title", title, "--body-file", body_file]
        else:
            command = ["gh", "pr", "create", "--base", base, "--head", branch, "--title", title, "--body-file", body_file]
        result = subprocess.run(command, cwd=cwd, text=True, encoding="utf-8", capture_output=True)
    finally:
        os.unlink(body_file)
    if result.returncode != 0:
        raise SystemExit(f"gh recusou o PR: {(result.stderr or result.stdout).strip()}")
    created = gh_pr_find(cwd, branch)
    if created is None:
        raise SystemExit("PR criado, mas `gh pr view` nao o encontrou.")
    return {"number": created["number"], "url": created["url"]}


def gh_pr_comment(cwd: Path, number: int, body: str) -> None:
    """Comenta no PR (corpo por arquivo, nunca por argumento)."""
    if _fixture() is not None:
        path = Path(os.environ[FIXTURE_ENV] + ".comments.json")
        comments = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        comments.append({"number": number, "body": body})
        path.write_text(json.dumps(comments, ensure_ascii=False), encoding="utf-8")
        return
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as handle:
        handle.write(body)
        body_file = handle.name
    try:
        result = subprocess.run(
            ["gh", "pr", "comment", str(number), "--body-file", body_file],
            cwd=cwd, text=True, encoding="utf-8", capture_output=True,
        )
    finally:
        os.unlink(body_file)
    if result.returncode != 0:
        raise SystemExit(f"gh recusou o comentario: {(result.stderr or result.stdout).strip()}")


def _save_fixture_prs(prs: list[dict[str, Any]]) -> None:
    _fixture_prs_path().write_text(json.dumps(prs, ensure_ascii=False), encoding="utf-8")


def _fixture_pr(number: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    prs = _fixture_prs()
    entry = next((pr for pr in prs if pr["number"] == number), None)
    if entry is None:
        raise SystemExit(f"PR #{number} nao existe no fixture.")
    return prs, entry


def _gh_json(cwd: Path, *args: str) -> Any:
    result = subprocess.run(["gh", *args], cwd=cwd, text=True, encoding="utf-8", capture_output=True)
    if result.returncode != 0:
        raise SystemExit(f"gh {' '.join(args[:3])} falhou: {(result.stderr or result.stdout).strip()}")
    return json.loads(result.stdout)


def gh_pr_state(cwd: Path, number: int) -> dict[str, Any]:
    """{state, head, mergeState} do PR (D-127)."""
    if _fixture() is not None:
        _prs, entry = _fixture_pr(number)
        return {"state": entry.get("state", "OPEN"), "head": entry.get("head"), "mergeState": entry.get("mergeState", "CLEAN")}
    data = _gh_json(cwd, "pr", "view", str(number), "--json", "state,headRefOid,mergeStateStatus")
    return {"state": data["state"], "head": data["headRefOid"], "mergeState": data["mergeStateStatus"]}


def gh_pr_update_branch(cwd: Path, number: int) -> tuple[str | None, str | None]:
    """Rebase da branch do PR na base: (head novo, erro)."""
    if _fixture() is not None:
        prs, entry = _fixture_pr(number)
        after = entry.get("afterUpdate") or {}
        if after.get("conflict"):
            return None, "conflito no rebase com a base"
        entry["head"] = after.get("head", entry.get("head"))
        entry["checks"] = after.get("checks", entry.get("checks"))
        entry["mergeState"] = "CLEAN"
        _save_fixture_prs(prs)
        return entry["head"], None
    result = subprocess.run(
        ["gh", "pr", "update-branch", str(number), "--rebase"],
        cwd=cwd, text=True, encoding="utf-8", capture_output=True,
    )
    if result.returncode != 0:
        return None, (result.stderr or result.stdout).strip() or "update-branch falhou"
    return gh_pr_state(cwd, number)["head"], None


# --- leitura dos checks (D-201) --------------------------------------------
#
# `gh pr checks --required` so devolve array quando o repositorio tem politica
# de checks obrigatorios. Sem protecao de branch ele sai com rc=1 e "no required
# checks reported on the '<branch>' branch": a lista ficava vazia, o `all(...)`
# era falso para sempre e o veredito morria em `pending` - nenhum item da fila
# mergeava (medido no backend-simulators em 29/10/2026, com o GitHub dizendo
# `mergeStateStatus CLEAN` o tempo todo).
#
# "Nao existe politica de obrigatorios" e estado **estavel** - esperar nao muda
# nada. "Os obrigatorios ainda nao reportaram" e **transitorio**. Sao casos
# diferentes, e agora o log diz qual deles foi detectado.

CHECKS_FALLBACK, CHECKS_STRICT = "fallback", "strict"
NO_CHECKS_WAIT, NO_CHECKS_MERGE = "wait", "merge"

CASE_REQUIRED = "obrigatorios"
CASE_NO_POLICY = "sem-politica"
CASE_SILENT = "sem-check"
CASE_GH_ERROR = "erro-gh"

PASSING_BUCKETS = ("pass", "skipping")
_NO_REQUIRED_RE = re.compile(r"no required checks reported", re.IGNORECASE)
_NO_CHECKS_RE = re.compile(r"no checks reported", re.IGNORECASE)


class GhRun(NamedTuple):
    """Chamada ao `gh`, crua - com o `returncode` e o `stderr` que o leitor antigo jogava fora."""

    returncode: int = 0
    stdout: str = ""
    stderr: str = ""


class ChecksReading(NamedTuple):
    """Veredito dos checks de um PR e o caso que o produziu (para o log da fila)."""

    verdict: str
    failing: list[str]
    case: str
    detail: str


def _as_array(stdout: str) -> list[dict[str, Any]]:
    """Lista do `gh --json`, ou vazia quando a saida nao e um array."""
    text = (stdout or "").strip()
    if not text.startswith("["):
        return []
    try:
        parsed = json.loads(text)
    except ValueError:
        return []
    return parsed if isinstance(parsed, list) else []


def _bucket_reading(checks: list[dict[str, Any]], case: str, note: str) -> ChecksReading:
    """Veredito de uma lista de checks ja reportados.

    `cancel` nao conta como vermelho: check cancelado e ausencia de prova, nao
    prova de falha (mesma regra do `read_commit_runs`). Sem veredito o item
    espera - nao volta ao autor por algo que ninguem mediu.
    """
    failing = [c.get("name") or "?" for c in checks if c.get("bucket") == "fail"]
    if failing:
        return ChecksReading("fail", failing, case, f"{note}; vermelho em {', '.join(failing)}")
    silent = [f"{c.get('name') or '?'} ({c.get('bucket')})" for c in checks
              if c.get("bucket") not in PASSING_BUCKETS]
    if silent:
        return ChecksReading("pending", [], case, f"{note}; ainda sem veredito em {', '.join(silent)}")
    return ChecksReading("pass", [], case, f"{note}; todos verdes")


def read_pr_checks(required: GhRun, plain_of: Callable[[], GhRun],
                   policy: str = CHECKS_FALLBACK) -> ChecksReading:
    """Veredito dos checks do PR a partir das respostas cruas do `gh`.

    Havendo politica de obrigatorios, ela manda. Sem ela, a pergunta que resta
    e a mesma que o `read_commit_runs` ja faz e que funciona: *o que rodou
    terminou verde?* - mas so quando algo rodou, e um vermelho qualquer
    continua barrando o merge. Quem nega o merge por falta de protecao segue
    sendo o `mergeStateStatus` do GitHub, conferido no executor.
    `delivery.queue.requiredChecks = strict` recusa esse recuo.
    """
    checks = _as_array(required.stdout)
    if checks:
        return _bucket_reading(checks, CASE_REQUIRED, f"{len(checks)} checks obrigatorios")
    message = (required.stderr or required.stdout).strip()
    if required.returncode != 0 and not _NO_REQUIRED_RE.search(message) and not _NO_CHECKS_RE.search(message):
        first = (message.splitlines() or ["erro"])[0]
        return ChecksReading("pending", [], CASE_GH_ERROR, f"`gh pr checks` falhou: {first}")
    reported = _as_array(plain_of().stdout)
    if not reported:
        return ChecksReading("pending", [], CASE_SILENT, "nenhum check reportou neste PR")
    if policy == CHECKS_STRICT:
        return ChecksReading("pending", [], CASE_NO_POLICY,
                             f"sem politica de checks obrigatorios e requiredChecks=strict: "
                             f"os {len(reported)} checks reportados nao contam")
    return _bucket_reading(reported, CASE_NO_POLICY,
                           f"sem politica de checks obrigatorios; julgado pelos {len(reported)} que rodaram")


def settle(reading: ChecksReading, no_checks: str = NO_CHECKS_WAIT) -> ChecksReading:
    """Fim do prazo: repositorio que nao reporta check algum e decisao do dono.

    `delivery.queue.noChecks`: `wait` (padrao) deixa o item esperando e diz por
    que; `merge` libera - o dono assume que ali nao ha nada a provar. Nenhum
    dos dois alcanca check vermelho ou check que so esta atrasado.
    """
    if reading.case == CASE_SILENT and no_checks == NO_CHECKS_MERGE:
        return reading._replace(verdict="pass",
                                detail="nenhum check reportou; delivery.queue.noChecks=merge libera")
    return reading


def _gh_run(cwd: Path, *args: str) -> GhRun:
    result = subprocess.run(["gh", *args], cwd=cwd, text=True, encoding="utf-8", capture_output=True)
    return GhRun(result.returncode, result.stdout or "", result.stderr or "")


def _scripted_run(script: dict[str, Any] | None) -> GhRun:
    """Resposta do `gh` roteirizada no fixture: `{"rc": 1, "stderr": "..."}` ou
    `{"stdout": [{...}]}` (lista vira JSON, como `gh --json` devolveria)."""
    if script is None:
        return GhRun(1, "", "no checks reported on the 'fixture' branch")
    stdout = script.get("stdout", "")
    return GhRun(int(script.get("rc", 0)),
                 stdout if isinstance(stdout, str) else json.dumps(stdout),
                 script.get("stderr", ""))


def gh_pr_checks(cwd: Path, number: int, timeout_seconds: float, poll_seconds: float = 20.0,
                 policy: str = CHECKS_FALLBACK, no_checks: str = NO_CHECKS_WAIT) -> ChecksReading:
    """Espera os checks do PR e devolve o veredito com o caso que o produziu."""
    if _fixture() is not None:
        _prs, entry = _fixture_pr(number)
        scripted = entry.get("ghChecks")
        if scripted is not None:
            return settle(read_pr_checks(_scripted_run(scripted.get("required")),
                                         lambda: _scripted_run(scripted.get("plain")), policy), no_checks)
        verdict = entry.get("checks", "pass")
        return ChecksReading(verdict, list(entry.get("failing") or []), CASE_REQUIRED, f"roteirizado: {verdict}")
    deadline = time.monotonic() + timeout_seconds
    while True:
        reading = read_pr_checks(
            _gh_run(cwd, "pr", "checks", str(number), "--required", "--json", "name,bucket"),
            lambda: _gh_run(cwd, "pr", "checks", str(number), "--json", "name,bucket"),
            policy,
        )
        if reading.verdict in ("pass", "fail") or time.monotonic() > deadline:
            return settle(reading, no_checks)
        time.sleep(poll_seconds)


def gh_pr_merge(cwd: Path, number: int, head: str, subject: str, body: str) -> str | None:
    """Squash preso ao head (`--match-head-commit`); devolve o erro ou None."""
    if _fixture() is not None:
        prs, entry = _fixture_pr(number)
        if entry.get("head") != head:
            return f"o head mudou ({entry.get('head')})"
        if entry.get("mergeState", "CLEAN") not in ("CLEAN", "HAS_HOOKS", "UNSTABLE"):
            return "the base branch policy prohibits the merge"
        entry["merged"] = {"matchHead": head, "subject": subject, "body": body}
        # D-135: o roteiro pode trazer o squash real (para o diff da R7).
        entry["mergeCommit"] = entry.get("squashSha") or f"{number:040x}"
        entry["state"] = "MERGED"
        _save_fixture_prs(prs)
        return None
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as handle:
        handle.write(body)
        body_file = handle.name
    try:
        result = subprocess.run(
            ["gh", "pr", "merge", str(number), "--squash", "--match-head-commit", head,
             "--subject", subject, "--body-file", body_file],
            cwd=cwd, text=True, encoding="utf-8", capture_output=True,
        )
    finally:
        os.unlink(body_file)
    return None if result.returncode == 0 else (result.stderr or result.stdout).strip() or "merge falhou"


def gh_pr_merge_commit(cwd: Path, number: int) -> str | None:
    """SHA do commit de squash na base (D-128)."""
    if _fixture() is not None:
        _prs, entry = _fixture_pr(number)
        return entry.get("mergeCommit")
    data = _gh_json(cwd, "pr", "view", str(number), "--json", "mergeCommit")
    return (data.get("mergeCommit") or {}).get("oid")


CI_GREEN = ("success", "skipped", "neutral")
CI_NO_PROOF = ("cancelled", "canceled", "stale")


class CiReading(NamedTuple):
    """Veredito do CI de um commit e o que o sustenta (para o log da fila)."""

    verdict: str
    failing: list[str]
    detail: str


def read_commit_runs(runs: list[dict[str, Any]]) -> CiReading:
    """Veredito do CI de um commit a partir dos runs do `gh run list` (D-201).

    `cancelled`/`stale` e **ausencia de prova**, nao prova de falha: com
    `cancel-in-progress`, o merge seguinte cancela o run do anterior em
    segundos. Contar isso como vermelho congelou a fila por uma main verde -
    4 merges em 21 s deixaram 3 runs cancelados, e foi preciso `queue resume` +
    `queue run` tres vezes para reconciliar. Sem prova nao se aprova nem se
    reprova: o veredito e `pending`, o executor avisa com o nome dos runs e
    segue, e o auto-finish da R7 (que exige `main verde == pass`) continua nao
    fechando a demanda sozinho. `timed_out` e `failure` seguem vermelhos.
    """
    if not runs:
        return CiReading("pending", [], "nenhum run no commit")
    done = [run for run in runs if run.get("status") == "completed"]
    failing = [run.get("name") or "?" for run in done
               if run.get("conclusion") not in CI_GREEN and run.get("conclusion") not in CI_NO_PROOF]
    if failing:
        return CiReading("fail", failing, f"vermelho em {', '.join(failing)}")
    if len(done) != len(runs):
        return CiReading("pending", [], f"{len(runs) - len(done)} de {len(runs)} runs ainda rodando")
    no_proof = [f"{run.get('name') or '?'} ({run.get('conclusion')})" for run in done
                if run.get("conclusion") in CI_NO_PROOF]
    if no_proof:
        return CiReading("pending", [], f"sem prova: {', '.join(no_proof)}; os demais verdes")
    return CiReading("pass", [], f"{len(done)} runs verdes")


def gh_commit_ci(cwd: Path, sha: str, timeout_seconds: float, poll_seconds: float = 30.0) -> CiReading:
    """CI dos workflows no commit `sha` da base.

    O CI do PR prova o PR; o da main prova a combinacao (D-128).
    """
    if _fixture() is not None:
        entry = next((pr for pr in _fixture_prs() if pr.get("mergeCommit") == sha), {})
        if entry.get("mainRuns") is not None:
            return read_commit_runs(entry["mainRuns"])
        verdict = entry.get("mainCi", "pass")
        return CiReading(verdict, (["ci da main"] if verdict == "fail" else []), f"roteirizado: {verdict}")
    deadline = time.monotonic() + timeout_seconds
    while True:
        result = subprocess.run(
            ["gh", "run", "list", "--commit", sha, "--json", "name,status,conclusion"],
            cwd=cwd, text=True, encoding="utf-8", capture_output=True,
        )
        reading = read_commit_runs(_as_array(result.stdout) if result.returncode == 0 else [])
        if reading.verdict in ("pass", "fail") or time.monotonic() > deadline:
            return reading
        time.sleep(poll_seconds)


def _fixture_closed_path() -> Path:
    return Path(os.environ[FIXTURE_ENV] + ".closed.json")


def gh_bot_prs(cwd: Path) -> list[dict[str, Any]]:
    """PRs abertos do Dependabot: numero, titulo, rotulos, arquivos e diff (D-129)."""
    fixture = _fixture()
    if fixture is not None:
        path = _fixture_closed_path()
        closed = {c["number"] for c in json.loads(path.read_text(encoding="utf-8"))} if path.exists() else set()
        return [pr for pr in fixture.get("__dependabot__", []) if pr["number"] not in closed]
    prs = _gh_json(cwd, "pr", "list", "--author", "app/dependabot", "--state", "open",
                   "--json", "number,title,labels,files")
    result = []
    for pr in prs:
        diff = subprocess.run(["gh", "pr", "diff", str(pr["number"])], cwd=cwd, text=True,
                              encoding="utf-8", errors="replace", capture_output=True)
        result.append({
            "number": pr["number"],
            "title": pr.get("title", ""),
            "labels": [label.get("name", "") for label in pr.get("labels") or []],
            "files": [f.get("path", "") for f in pr.get("files") or []],
            "diff": diff.stdout if diff.returncode == 0 else "",
        })
    return result


def gh_labeled_prs(cwd: Path, label: str) -> list[dict[str, Any]]:
    """PRs abertos com o rotulo `label`: numero, titulo, branch e head (D-130)."""
    fixture = _fixture()
    if fixture is not None:
        return list(fixture.get("__labeled__", []))
    return _gh_json(cwd, "pr", "list", "--label", label, "--state", "open",
                    "--json", "number,title,headRefName,headRefOid")


def gh_pr_close(cwd: Path, number: int, comment: str) -> None:
    """Fecha o PR com um comentario (D-129: PR do bot incorporado ao lote)."""
    if _fixture() is not None:
        path = _fixture_closed_path()
        closed = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        closed.append({"number": number, "comment": comment})
        path.write_text(json.dumps(closed, ensure_ascii=False), encoding="utf-8")
        return
    state = _gh_json(cwd, "pr", "view", str(number), "--json", "state")
    if state.get("state") != "OPEN":
        return
    subprocess.run(["gh", "pr", "close", str(number), "--comment", comment],
                   cwd=cwd, text=True, encoding="utf-8", capture_output=True)


def pr_patch_id(cwd: Path, number: int, head: str, base_branch: str) -> str | None:
    """Patch-id do PR no `head` (R8): igual = mesmo conteudo, mesmo apos rebase."""
    if _fixture() is not None:
        _prs, entry = _fixture_pr(number)
        return (entry.get("patchIds") or {}).get(head)
    from _audit import patch_id  # import tardio: _audit importa este modulo

    subprocess.run(["git", "fetch", "-q", "origin", base_branch, f"refs/pull/{number}/head"], cwd=cwd, capture_output=True)
    return patch_id(cwd, f"origin/{base_branch}", head)


__all__ = [
    "CASE_GH_ERROR",
    "CASE_NO_POLICY",
    "CASE_REQUIRED",
    "CASE_SILENT",
    "CHECKS_FALLBACK",
    "CHECKS_STRICT",
    "FIXTURE_ENV",
    "NO_CHECKS_MERGE",
    "NO_CHECKS_WAIT",
    "ChecksReading",
    "CiReading",
    "GhRun",
    "gh_api",
    "gh_bot_prs",
    "gh_commit_ci",
    "gh_labeled_prs",
    "gh_pr_checks",
    "gh_pr_close",
    "gh_pr_comment",
    "gh_pr_find",
    "gh_pr_merge",
    "gh_pr_merge_commit",
    "gh_pr_state",
    "gh_pr_update_branch",
    "gh_pr_upsert",
    "gh_status",
    "pr_patch_id",
    "read_commit_runs",
    "read_pr_checks",
    "repo_slug",
    "settle",
]
