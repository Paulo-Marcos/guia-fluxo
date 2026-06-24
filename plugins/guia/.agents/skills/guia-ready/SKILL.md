---
name: guia-ready
description: HANDOFF to developer validation — does NOT close the task. **The agent runs this itself when implementation ends**, never the human. The gate that forces human-in-the-loop before `finish`. Options: `--file <path>` (changed files, repeatable), `--summary "<note>"` (implementation notes, repeatable), `--validation "<cmd>"` (validations that passed, repeatable), `--pending "<gap>"` (manual checks still needed, repeatable). To close after validation use `finish`; to inspect without changing state use `status`.
---

# Ready

**The agent (you) calls this when implementation ends** — not the human. `ready` is the handoff to human validation; the human then validates in real use, and you call `finish` afterward. Do not skip `ready` and go straight to `finish` — that bypasses the human-in-the-loop gate.

**Run the engine** via the repo wrapper (portable fallback on Linux/Mac/no PowerShell: `python core/src/guia.py <command>`):

```powershell
.\core\bin\guia.ps1 <command>
```

Substitute `<command>` with the verb and arguments for this skill:

```text
ready <D-NNN> --file path/to/file --summary "What changed" --validation "What passed"
```

Pass changed files with `--file`, implementation notes with `--summary`, validation commands run with `--validation`, and manual gaps still pending with `--pending`.

### Convencao de commit do usuario (D-054)

Antes de entregar, **verifique se existe uma skill de convencao de commits** do usuario/projeto — qualquer skill cujo nome ou descricao combine `commit` com `conventional`, `convention` ou `gitmoji` (ex.: `conventional-commit-gitmoji`). Olhe as skills disponiveis na sessao e em `.claude/`/plugins.

- **Se houver uma**: rode-a para gerar o **subject** do commit seguindo a convencao do usuario e passe pronto via `--commit-subject "<subject>"`. Ele substitui o header padrao do engine (`{kind}({id}): {title}`); o corpo (summary/validacoes/arquivos) e o rodape `Task: {id}` sao preservados pelo engine. Mantenha o id da task no subject quando a convencao permitir.
- **Se houver mais de uma candidata e a escolha for ambigua**: pergunte ao usuario qual usar antes de gerar.
- **Se nao houver nenhuma**: nao passe `--commit-subject`; o engine usa o formato Conventional Commits padrao.

O subject e persistido na task e o `finish` (humano) o consome automaticamente — voce nao reconstroi nada depois.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DA DEMANDA: ...` line printed by the script — do not paraphrase or translate it. It names the **current demand**, not the chat: one chat may hold several demandas (e.g. an epic D-049 and its stories), so the line is pure demand info, not a chat title.
3. **Optional — rename the chat only if it helps.** The print does not rename anything; renaming is a convenience, never required. **Codex App:** when the thread tools are loaded and this chat tracks a single demand, call `codex_app.list_threads` to find the current thread id, then `codex_app.set_thread_title` with the demand title. Skip the rename when the chat holds multiple demandas. If the tools are not loaded, search for thread tools first.
4. **Antigravity (no thread API):** nothing to rename programmatically — the printed line is enough.
5. If shell access fails, surface the exact command the developer can run by hand instead of silently failing.

Then **stop and wait** for the developer to validate. Do not run `finish` until the developer confirms validation in real use.
