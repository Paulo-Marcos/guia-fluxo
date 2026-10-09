---
description: "QUEUE — show the merge queue (order, state, why each item waits; `--json`), put an audited PR in it (`add [D-NNN] [--priority hotfix]`, requires the approved audit on the current head; at level >= `queue` it enters approved unless something in `alwaysHuman` holds it), or bring labeled cloud PRs in (`import`). Agent may `add` at level >= `queue`. For pause/resume/remove/priority/run use `queue-control` (user-only); for the merge ok use `approve`."
---

# Queue

The chat launches (`ship` -> `audit` -> `queue add`) and is free; one executor integrates one PR at a time.

**Run the engine.** It ships inside the plugin — no repo clone, no manual `init`. Invoke it through `${CLAUDE_PLUGIN_ROOT}` (the plugin install dir), never a path relative to the working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>      # bash (canonical — you call via the Bash tool)
python "$env:CLAUDE_PLUGIN_ROOT/bin/guia.py" <command>    # PowerShell
```

The engine roots itself at the current project and auto-creates `.guia/` there on the first command. Substitute `<command>` with the verb and arguments for this skill:

```text
queue                     # list, with the reason each item waits
queue add [D-NNN] [--priority hotfix]
queue import              # PRs labeled guia:fila from the cloud (no audit yet)
```

- If `add` prints `alwaysHuman: ...`, the item waits for the developer's `approve`: tell them the reason.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DA DEMANDA: ...` line printed by the script — do not paraphrase or translate it. It identifies the **current demand**, not the chat: a single chat may hold several demandas (e.g. an epic D-049 and its stories), so the line is pure demand info, not a chat title.
3. **Optional — rename the chat only if it actually helps navigation.** The print does *not* rename the chat; renaming is a user-facing convenience, never required. When this chat tracks a single demand and a rename would help the developer, call `mark_chapter` (`mcp__ccd_session__mark_chapter`) with the demand title (also places a divider + ToC entry) and/or try `/rename <title>` if this build exposes it. Skip the rename when the chat already holds multiple demandas — renaming to one demand's title would mislead.
