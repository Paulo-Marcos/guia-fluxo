---
description: "HANDOFF TO PR — from the demand's worktree (`delivery.mode: pr`), run the full gate, check the changelog fragment and the Request -> Test table, push, open or update the PR (title = commit subject, body built from the demand) and save the squash message to `.guia/queue/D-NNN.msg` (with `[unlock:]` marks computed from the branch diff and `Co-Authored-By`); status -> `Em PR`. Options: `--subject`, `--body \"<why>\"`, `--unlock-reason \"<lock>=<reason>\"`, `--no-changelog \"<reason>\"`. Agent at autonomy level >= `pr`. Before: `ready`; after: `audit`."
---

# Ship

Take the demand from its worktree to a pull request. All checks run before any effect: if one refuses, nothing was pushed and the state did not change.

**Run the engine.** It ships inside the plugin — no repo clone, no manual `init`. Invoke it through `${CLAUDE_PLUGIN_ROOT}` (the plugin install dir), never a path relative to the working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>      # bash (canonical — you call via the Bash tool)
python "$env:CLAUDE_PLUGIN_ROOT/bin/guia.py" <command>    # PowerShell
```

The engine roots itself at the current project and auto-creates `.guia/` there on the first command. Substitute `<command>` with the verb and arguments for this skill:

```text
ship [D-NNN] --subject "<emoji> <type>(D-NNN): <title>" --body "<why>" --unlock-reason "<reason>"
```

- Commit first (`commit-message` builds the message); ship pushes what is committed.
- Without an id, the demand comes from the `d-NNN-*` branch.
- Next step: `audit` on the new head.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DA DEMANDA: ...` line printed by the script — do not paraphrase or translate it. It identifies the **current demand**, not the chat: a single chat may hold several demandas (e.g. an epic D-049 and its stories), so the line is pure demand info, not a chat title.
3. **Optional — rename the chat only if it actually helps navigation.** The print does *not* rename the chat; renaming is a user-facing convenience, never required. When this chat tracks a single demand and a rename would help the developer, call `mark_chapter` (`mcp__ccd_session__mark_chapter`) with the demand title (also places a divider + ToC entry) and/or try `/rename <title>` if this build exposes it. Skip the rename when the chat already holds multiple demandas — renaming to one demand's title would mislead.
