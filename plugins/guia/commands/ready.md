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

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Always call `mark_chapter`** (`mcp__ccd_session__mark_chapter`) with that title — this is the reliable rename surrogate in Claude Code: it places a visible divider in the transcript and a ToC entry the developer can jump to. Works on every Claude Code build that has the `ccd_session` MCP loaded.
4. **Also try `/rename <suggested-title>`** if this Claude Code build exposes the slash command. No harm if it doesn't — `mark_chapter` already covers the navigation need; this is bonus sidebar rename when supported.
5. If neither path works, print the title prominently as a final fallback.

Then **stop and wait** for the developer to validate. Do not run `finish` until the developer confirms validation in real use.
