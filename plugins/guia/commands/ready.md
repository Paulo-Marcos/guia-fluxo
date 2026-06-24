---
description: HANDOFF to developer validation — does NOT close the task. **The agent runs this itself when implementation ends**, never the human. The gate that forces human-in-the-loop before `finish`. Options: `--file <path>` (changed files, repeatable), `--summary "<note>"` (implementation notes, repeatable), `--validation "<cmd>"` (validations that passed, repeatable), `--pending "<gap>"` (manual checks still needed, repeatable). To close after validation use `finish`; to inspect without changing state use `status`.
---

# Ready

**The agent (you) calls this when implementation ends** — not the human. `ready` is the handoff to human validation; the human then validates in real use, and you call `finish` afterward. Do not skip `ready` and go straight to `finish` — that bypasses the human-in-the-loop gate.

**Run the engine.** It ships inside the plugin — no repo clone, no manual `init`. Invoke it through `${CLAUDE_PLUGIN_ROOT}` (the plugin install dir), never a path relative to the working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>      # bash (canonical — you call via the Bash tool)
python "$env:CLAUDE_PLUGIN_ROOT/bin/guia.py" <command>    # PowerShell
```

The engine roots itself at the current project and auto-creates `.guia/` there on the first command. Substitute `<command>` with the verb and arguments for this skill:

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
2. Repeat the exact `NOME DA DEMANDA: ...` line printed by the script — do not paraphrase or translate it. It identifies the **current demand**, not the chat: a single chat may hold several demandas (e.g. an epic D-049 and its stories), so the line is pure demand info, not a chat title.
3. **Optional — rename the chat only if it actually helps navigation.** The print does *not* rename the chat; renaming is a user-facing convenience, never required. When this chat tracks a single demand and a rename would help the developer, call `mark_chapter` (`mcp__ccd_session__mark_chapter`) with the demand title (also places a divider + ToC entry) and/or try `/rename <title>` if this build exposes it. Skip the rename when the chat already holds multiple demandas — renaming to one demand's title would mislead.

Then **stop and wait** for the developer to validate. Do not run `finish` until the developer confirms validation in real use.
