---
description: START — begin work on a `Planejada` or `Backlog` task (status → `Em desenvolvimento`). Assumes triage is done (kind already decided); use `promote` when kind still needs deciding. Options: `--note "<starting note>"`. To resume from `Bloqueada` use `unblock`; to create a fresh task use `feature`/`bug`/`chore`.
---

# Start

**Start work on a Planejada task (or directly from the Backlog).** Moves status to `Em desenvolvimento`. Assumes triage (kind = feature/bug/chore) is done — if you still need to decide the kind, use `$promote`.

**Run the engine.** It ships inside the plugin — no repo clone, no manual `init`. Invoke it through `${CLAUDE_PLUGIN_ROOT}` (the plugin install dir), never a path relative to the working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>      # bash (canonical — you call via the Bash tool)
python "$env:CLAUDE_PLUGIN_ROOT/bin/guia.py" <command>    # PowerShell
```

The engine roots itself at the current project and auto-creates `.guia/` there on the first command. Substitute `<command>` with the verb and arguments for this skill:

```text
start <D-NNN> [--note "Starting now because..."]
```

Distinct from:
- `$promote <B-NNN>`: triage a backlog item deciding kind and plan before starting.
- `$plan`: mark as triaged without starting.
- `$feature/$bug/$chore` (new tasks): create a fresh task already `Em desenvolvimento`.

Accepts transition from `Backlog` (shortcut that skips `Planejada`) or `Planejada`. Fails if the task is already `Em desenvolvimento`, in a terminal state (`Validada`, `Finalizada`, `Cancelada`), or `Bloqueada` (use `$unblock`).

Tasks promoted from `Backlog` enter `.guia/DEMANDAS.md`.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DA DEMANDA: ...` line printed by the script — do not paraphrase or translate it. It identifies the **current demand**, not the chat: a single chat may hold several demandas (e.g. an epic D-049 and its stories), so the line is pure demand info, not a chat title.
3. **Optional — rename the chat only if it actually helps navigation.** The print does *not* rename the chat; renaming is a user-facing convenience, never required. When this chat tracks a single demand and a rename would help the developer, call `mark_chapter` (`mcp__ccd_session__mark_chapter`) with the demand title (also places a divider + ToC entry) and/or try `/rename <title>` if this build exposes it. Skip the rename when the chat already holds multiple demandas — renaming to one demand's title would mislead.
