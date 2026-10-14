---
name: guia-block
description: "PAUSE an in-flight task — preserves WIP and moves status to `Bloqueada`. Use when the task will return: waiting on a decision, external dependency, priority swap. Required: `--reason \"<motive>\"` (recorded in `task.blocks[]`). To resume use `unblock`; for terminal close use `cancel`; for handoff to validation use `ready`."
---

# Block

**Pause the current task with a mandatory reason.** Moves status to `Bloqueada`, preserves the WIP, and keeps the entry in `.guia/DEMANDAS.md`. Use to stop temporarily: external dependency, waiting on a decision, priority swap. Distinct from `cancel` (terminal, does not return) and `finish` (validated and closed).

**Run the engine** via the repo wrapper (portable fallback on Linux/Mac/no PowerShell: `python core/src/guia.py <command>`):

```powershell
.\core\bin\guia.ps1 <command>
```

Substitute `<command>` with the verb and arguments for this skill:

```text
block <D-NNN> --reason "Why pausing"
```

`--reason` is **required** (recorded in `task.blocks[]` for blocked-time auditing).

Fails if the task is already in a terminal state (`Validada`, `Finalizada`, `Cancelada`) or already in `Bloqueada`.

To resume, use the `unblock` verb (`unblock <D-NNN>`).

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DA DEMANDA: ...` line printed by the script — do not paraphrase or translate it. It names the **current demand**, not the chat: one chat may hold several demandas (e.g. an epic D-049 and its stories), so the line is pure demand info, not a chat title.
3. **Name the chat and record it (D-157).** Run `chat <D-NNN>` for the stable name (`NOME DO CHAT: ...`). **Codex App:** when the thread tools are loaded and this chat is dedicated to the demand, call `codex_app.list_threads` to find the current thread id, then `codex_app.set_thread_title` with that name (search for the thread tools first if they are not loaded). When the chat already holds other demandas, do not rename it; use the name it already has. Either way record it with `chat <D-NNN> --title "<name>"` and show the name to the developer - the queue and `status --all` cite it so they can come back.
4. **Antigravity (no thread API):** nothing to rename programmatically — the printed line is enough.
5. If shell access fails, surface the exact command the developer can run by hand instead of silently failing.
6. **Recommend the model for this demand (D-153)** — when the demand is created or started in this chat: from what you read in the request and the code, run `triage <D-NNN> --scope <areas> [--risk auth|migration|concurrency|security|prod|data] [--uncertain] [--irreversible]` and show the `MODELO RECOMENDADO ...` line. If this chat runs on a different model, say so plainly - switching is the developer's call. A Fable suggestion is only a suggestion: ask before using it. The audit never runs below Opus.
7. **Record the model actually used (D-154)** — once per chat: `model <D-NNN> --who chat --model <haiku|sonnet|opus|fable> --purpose "<what this chat did>"`. When you delegate to a subagent, pick its model by what it does (locate/read code: haiku; a 1-2 file change: sonnet; review or audit: opus - never below) and record it the same way with `--who subagent`. Show the `MODELO USADO ...` line: the developer compares it with the recommendation (`model --summary`).
