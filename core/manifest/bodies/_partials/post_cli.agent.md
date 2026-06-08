## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DO CHAT: ...` line printed by the script — do not paraphrase or translate it.
3. **Codex App:** if the thread tools are loaded, call `codex_app.list_threads` to find the current thread id, then call `codex_app.set_thread_title` with the title printed after `NOME DO CHAT:`. If the tools are not loaded, search for thread tools first.
4. **Antigravity (no thread API):** print the title prominently as best-effort — the host has no programmatic rename today.
5. If shell access fails, surface the exact command the developer can run by hand instead of silently failing.
