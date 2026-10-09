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
3. **Optional — rename the chat only if it helps.** The print does not rename anything; renaming is a convenience, never required. **Codex App:** when the thread tools are loaded and this chat tracks a single demand, call `codex_app.list_threads` to find the current thread id, then `codex_app.set_thread_title` with the demand title. Skip the rename when the chat holds multiple demandas. If the tools are not loaded, search for thread tools first.
4. **Antigravity (no thread API):** nothing to rename programmatically — the printed line is enough.
5. If shell access fails, surface the exact command the developer can run by hand instead of silently failing.
