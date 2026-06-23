## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DA DEMANDA: ...` line printed by the script — do not paraphrase or translate it. It names the **current demand**, not the chat: one chat may hold several demandas (e.g. an epic D-049 and its stories), so the line is pure demand info, not a chat title.
3. **Optional — rename the chat only if it helps.** The print does not rename anything; renaming is a convenience, never required. **Codex App:** when the thread tools are loaded and this chat tracks a single demand, call `codex_app.list_threads` to find the current thread id, then `codex_app.set_thread_title` with the demand title. Skip the rename when the chat holds multiple demandas. If the tools are not loaded, search for thread tools first.
4. **Antigravity (no thread API):** nothing to rename programmatically — the printed line is enough.
5. If shell access fails, surface the exact command the developer can run by hand instead of silently failing.
