---
description: PAUSE an in-flight task — preserves WIP and moves status to `Bloqueada`. Use when the task will return: waiting on a decision, external dependency, priority swap. Required: `--reason "<motive>"` (recorded in `task.blocks[]`). To resume use `unblock`; for terminal close use `cancel`; for handoff to validation use `ready`.
---

# Block

**Pause the current task with a mandatory reason.** Moves status to `Bloqueada`, preserves the WIP, and keeps the entry in `.guia/DEMANDAS.md`. Use to stop temporarily: external dependency, waiting on a decision, priority swap. Distinct from `cancel` (terminal, does not return) and `finish` (validated and closed).

**Run the engine.** It ships inside the plugin — no repo clone, no manual `init`. Invoke it through `${CLAUDE_PLUGIN_ROOT}` (the plugin install dir), never a path relative to the working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>      # bash (canonical — you call via the Bash tool)
python "$env:CLAUDE_PLUGIN_ROOT/bin/guia.py" <command>    # PowerShell
```

The engine roots itself at the current project and auto-creates `.guia/` there on the first command. Substitute `<command>` with the verb and arguments for this skill:

```text
block <D-NNN> --reason "Why pausing"
```

`--reason` is **required** (recorded in `task.blocks[]` for blocked-time auditing).

Fails if the task is already in a terminal state (`Validada`, `Finalizada`, `Cancelada`) or already in `Bloqueada`.

To resume, use the `unblock` verb (`unblock <D-NNN>`).

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DA DEMANDA: ...` line printed by the script — do not paraphrase or translate it. It identifies the **current demand**, not the chat: a single chat may hold several demandas (e.g. an epic D-049 and its stories), so the line is pure demand info, not a chat title.
3. **Optional — rename the chat only if it actually helps navigation.** The print does *not* rename the chat; renaming is a user-facing convenience, never required. When this chat tracks a single demand and a rename would help the developer, call `mark_chapter` (`mcp__ccd_session__mark_chapter`) with the demand title (also places a divider + ToC entry) and/or try `/rename <title>` if this build exposes it. Skip the rename when the chat already holds multiple demandas — renaming to one demand's title would mislead.
