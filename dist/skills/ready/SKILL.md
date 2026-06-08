---
name: ready
description: HANDOFF to developer validation — does NOT close the task. THE AGENT runs this when implementation is finished, NOT the human; it is the gate that forces human-in-the-loop before $finish. Triggered by /ready or "$ready" / "pronto para validar / enviar para teste". Marks the in-progress D-NNN as awaiting manual validation and records changed files, summary, and pending checks. Do NOT use for: closing an already-validated task (use $finish), or just inspecting the current task without changing its state (use $status).
---

# Ready

**The agent (you) calls this when implementation ends** — not the human. `ready` is the handoff to human validation; the human then validates in real use, and you call `finish` afterward. Do not skip `ready` and go straight to `finish` — that bypasses the human-in-the-loop gate (the reason `validate` was deprecated in F-003).

Run:

```powershell
.\core\bin\guia.ps1 ready <D-NNN> --file path/to/file --summary "What changed" --validation "What passed"
```

Pass changed files with `--file`, implementation notes with `--summary`, validation commands run with `--validation`, and manual gaps still pending with `--pending`.

Portable fallback (Linux/Mac/no PowerShell): `python core/src/guia.py ready <D-NNN> ...`.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Always call `mark_chapter`** (`mcp__ccd_session__mark_chapter`) with that title — this is the reliable rename surrogate in Claude Code: it places a visible divider in the transcript and a ToC entry the developer can jump to. Works on every Claude Code build that has the `ccd_session` MCP loaded.
4. **Also try `/rename <suggested-title>`** if this Claude Code build exposes the slash command. No harm if it doesn't — `mark_chapter` already covers the navigation need; this is bonus sidebar rename when supported.
5. If neither path works, print the title prominently as a final fallback.

Then **stop and wait** for the developer to validate. Do not run `finish` until the developer confirms validation in real use.
