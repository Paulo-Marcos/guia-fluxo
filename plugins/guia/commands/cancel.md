---
description: "TERMINAL CANCEL — closes the task with `status=Cancelada` (terminal, does not return). Use when the task will NOT be completed: created by mistake, scope dropped, wrong promote. Required: `--reason \"<motive>\"`. Options: `--keep-worktree` (default removes the worktree if present), `--set-current` (default clears current-task.json if the cancelled task was current). For a temporary pause that will resume use `block`; for a validated close use `finish`."
---

# Cancel

**Trigger by you (the agent) or the user, when the task will NOT be completed.** Marks the task as `Cancelada` (terminal) with a mandatory reason. Distinct from `block` (pause, will resume) and `finish` (validated and closed).

Typical cases:
- Demanda criada por engano.
- `promote` errado de um item de backlog.
- Mudanca de escopo: o que parecia uma feature/bug nao se justifica mais.

**Run the engine.** It ships inside the plugin — no repo clone, no manual `init`. Invoke it through `${CLAUDE_PLUGIN_ROOT}` (the plugin install dir), never a path relative to the working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>      # bash (canonical — you call via the Bash tool)
python "$env:CLAUDE_PLUGIN_ROOT/bin/guia.py" <command>    # PowerShell
```

The engine roots itself at the current project and auto-creates `.guia/` there on the first command. Substitute `<command>` with the verb and arguments for this skill:

```text
cancel <D-NNN> --reason "Motivo curto"
```

`--reason` is **required** (justification stays in history under `task.cancellations[]` and in `.guia/DEMANDAS.md`).

Useful flags:
- `--keep-worktree`: do not remove the associated worktree (default: remove if present).
- `--set-current`: keep the task as current after canceling (default: clear `.guia/current-task.json` if the canceled task was current).

Fails if the task is already in a terminal state (`Validada`, `Finalizada`, `Cancelada`).

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DA DEMANDA: ...` line printed by the script — do not paraphrase or translate it. It identifies the **current demand**, not the chat: a single chat may hold several demandas (e.g. an epic D-049 and its stories), so the line is pure demand info, not a chat title.
3. **Name the chat and record it (D-157)** — when this chat starts or resumes work on the demand, so the developer can come back to it when the queue returns it or leaves it pending:
   - Run `chat <D-NNN>`: it prints `NOME DO CHAT: ...`, a stable name without the status tag.
   - **Chat dedicated to this demand:** rename the session to that name — the session-title tool when this build has one, `mark_chapter` (`mcp__ccd_session__mark_chapter`, also places a divider + ToC entry), and/or `/rename <name>` — then record it: `chat <D-NNN> --title "<name>"`.
   - **Chat that already holds other demandas:** do not rename it to this demand (it would mislead); record the name the chat already has (the demand it started with): `chat <D-NNN> --title "<that name>"`.
   - **Always show the chat name to the developer**, even when renaming is not available, so it can be saved. The queue, `next` and `status --all` cite it ("volte ao chat: ...").
5. **Record the model actually used (D-154)** — once per chat: `model <D-NNN> --who chat --model <haiku|sonnet|opus|fable> --purpose "<what this chat did>"`. When you delegate to a subagent, pick its model by what it does (locate/read code: haiku; a 1-2 file change: sonnet; review or audit: opus - never below) and record it the same way with `--who subagent`. Show the `MODELO USADO ...` line: the developer compares it with the recommendation (`model --summary`).
