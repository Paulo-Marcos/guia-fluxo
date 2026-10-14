---
name: guia-ship
description: "HANDOFF TO PR — from the demand's worktree (`delivery.mode: pr`), run the full gate, check the changelog fragment and the Request -> Test table, push, open or update the PR (title = commit subject, body built from the demand) and save the squash message to `.guia/queue/D-NNN.msg` (with `[unlock:]` marks computed from the branch diff and `Co-Authored-By`); status -> `Em PR`. Options: `--subject`, `--body \"<why>\"`, `--unlock-reason \"<lock>=<reason>\"`, `--no-changelog \"<reason>\"`. Agent at autonomy level >= `pr`. Before: `ready`; after: `audit`."
---

# Ship

Take the demand from its worktree to a pull request. All checks run before any effect: if one refuses, nothing was pushed and the state did not change.

**Run the engine** via the repo wrapper (portable fallback on Linux/Mac/no PowerShell: `python core/src/guia.py <command>`):

```powershell
.\core\bin\guia.ps1 <command>
```

Substitute `<command>` with the verb and arguments for this skill:

```text
ship [D-NNN] --subject "<emoji> <type>(D-NNN): <title>" --body "<why>" --unlock-reason "<reason>"
```

- Commit first (`commit-message` builds the message); ship pushes what is committed.
- Without an id, the demand comes from the `d-NNN-*` branch.
- Next step: `audit` on the new head.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DA DEMANDA: ...` line printed by the script — do not paraphrase or translate it. It names the **current demand**, not the chat: one chat may hold several demandas (e.g. an epic D-049 and its stories), so the line is pure demand info, not a chat title.
3. **Name the chat and record it (D-157).** Run `chat <D-NNN>` for the stable name (`NOME DO CHAT: ...`). **Codex App:** when the thread tools are loaded and this chat is dedicated to the demand, call `codex_app.list_threads` to find the current thread id, then `codex_app.set_thread_title` with that name (search for the thread tools first if they are not loaded). When the chat already holds other demandas, do not rename it; use the name it already has. Either way record it with `chat <D-NNN> --title "<name>"` and show the name to the developer - the queue and `status --all` cite it so they can come back.
4. **Antigravity (no thread API):** nothing to rename programmatically — the printed line is enough.
5. If shell access fails, surface the exact command the developer can run by hand instead of silently failing.
6. **Record the model actually used (D-154)** — once per chat: `model <D-NNN> --who chat --model <haiku|sonnet|opus|fable> --purpose "<what this chat did>"`. When you delegate to a subagent, pick its model by what it does (locate/read code: haiku; a 1-2 file change: sonnet; review or audit: opus - never below) and record it the same way with `--who subagent`. Show the `MODELO USADO ...` line: the developer compares it with the recommendation (`model --summary`).
