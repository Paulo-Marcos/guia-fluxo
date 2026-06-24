---
description: CLOSE an already-validated task — runs the docs-check hook and commits by default. **`finish` is the USER's action: the agent only runs it when the developer requests `/guia:finish` or explicitly authorizes, and must NEVER trigger `finish` on its own — stop at `ready` and hand off. Behavioral rule, not a CLI parameter: no env, no flag (D-098 removed the `GUIA_HUMAN_FINISH` env gate the earlier D-080 had tried).** Use only after the developer confirms validation in real use. Required when `.guia/docs-map.yaml` exists: `--docs-touched <path>` (repeatable) or `--docs-skip "<reason>"`. Options: `--file`, `--summary`, `--validation` (same as ready), `--no-commit` (dry close), `--lock --lock-id <slug> --lock-description "..."` (protect files after close). For handoff to validation use `ready`; for inspection use `status`.
---

# Finish

Close an already-validated task. Run **only after** the developer confirms validation in real use — `finish` is the closing gate, not a shortcut.

> **`finish` is the USER's action (behavioral rule, D-098).** Closing is the developer's call. **If you are an AI agent, run `finish` ONLY when the developer requests `/guia:finish` or explicitly authorizes it — NEVER on your own initiative.** Your default job ends at `ready`: hand off and wait for the developer to ask for the close. This is a behavioral rule, not a CLI parameter — there is no env var or flag to set (D-098 removed the `GUIA_HUMAN_FINISH` env gate the earlier D-080 had tried; sending a variable was bad, and the engine cannot tell an agent apart from a human anyway).

**Run the engine.** It ships inside the plugin — no repo clone, no manual `init`. Invoke it through `${CLAUDE_PLUGIN_ROOT}` (the plugin install dir), never a path relative to the working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>      # bash (canonical — you call via the Bash tool)
python "$env:CLAUDE_PLUGIN_ROOT/bin/guia.py" <command>    # PowerShell
```

The engine roots itself at the current project and auto-creates `.guia/` there on the first command. Substitute `<command>` with the verb and arguments for this skill:

## 1) Docs hook (mandatory when `.guia/docs-map.yaml` exists)

Run the docs check before closing:

```text
docs-check
```

For each listed candidate:
- Open the file and decide if this task changes anything relevant to it.
- Update what makes sense (README pointer, CLI reference entry, CHANGELOG entry, ADR, explanation paragraph).
- Note the paths you touched.

If the project has no `.guia/docs-map.yaml`, the hook is a no-op and `finish` runs as before.

## 2) Close

Run this **only** because the developer asked for it (no env var or flag — see the rule above):

```text
finish <D-NNN> --docs-touched docs/reference/cli.md --docs-touched CHANGELOG.md
# or, when nothing needed touching:
finish <D-NNN> --docs-skip "internal flow, no user-facing change"
```

`finish` commits by default. Use `--no-commit` for dry close. Lock with `--lock --lock-id feature-slug --lock-description "..."` only when the developer asks for it.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DA DEMANDA: ...` line printed by the script — do not paraphrase or translate it. It identifies the **current demand**, not the chat: a single chat may hold several demandas (e.g. an epic D-049 and its stories), so the line is pure demand info, not a chat title.
3. **Optional — rename the chat only if it actually helps navigation.** The print does *not* rename the chat; renaming is a user-facing convenience, never required. When this chat tracks a single demand and a rename would help the developer, call `mark_chapter` (`mcp__ccd_session__mark_chapter`) with the demand title (also places a divider + ToC entry) and/or try `/rename <title>` if this build exposes it. Skip the rename when the chat already holds multiple demandas — renaming to one demand's title would mislead.

## File locks

Before editing files, honor `.guia/locks/registry.yaml`. If a target file is locked:

1. **Stop** before the edit.
2. **Explain to the developer**, in this order:
   - The lock id and which functionality it protects.
   - Why the planned edit is needed.
   - Expected impact (what changes, who notices).
   - Regression risk (what could break that is currently working).
   - Alternatives (route the change through a different file, scope reduction, etc.).
3. **Ask** for explicit authorization to proceed (or to unlock).
4. Only after the developer authorizes, edit — or use `python core/lock/check-lock.py unlock <id>` if the developer asks for the lock to be removed.

Never bypass a lock silently. The hook at commit time will reject the commit anyway, and the developer loses trust if the agent treats locks as advisory.

Task is closed.
