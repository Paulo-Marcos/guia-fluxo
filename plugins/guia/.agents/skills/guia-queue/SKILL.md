---
name: guia-queue
description: "QUEUE — show the merge queue (order, state, why each item waits; `--json`), put an audited PR in it (`add [D-NNN] [--priority hotfix]`, requires the approved audit on the current head; at level >= `queue` it enters approved unless something in `alwaysHuman` holds it), or bring labeled cloud PRs in (`import`). Agent may `add` at level >= `queue`. For pause/resume/remove/priority/run use `queue-control` (user-only); for the merge ok use `approve`."
---

# Queue

The chat launches (`ship` -> `audit` -> `queue add`) and is free; one executor integrates one PR at a time.

**Run the engine** via the repo wrapper (portable fallback on Linux/Mac/no PowerShell: `python core/src/guia.py <command>`):

```powershell
.\core\bin\guia.ps1 <command>
```

Substitute `<command>` with the verb and arguments for this skill:

```text
queue                     # list, with the reason each item waits
queue add [D-NNN] [--priority hotfix]
queue import              # PRs labeled guia:fila from the cloud (no audit yet)
```

- If `add` prints `alwaysHuman: ...`, the item waits for the developer's `approve`: tell them the reason.

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DA DEMANDA: ...` line printed by the script — do not paraphrase or translate it. It names the **current demand**. One demand per chat (D-185): a demand that comes up while working another (an epic story, a follow-up, a bug found on the way) is created with the CLI and worked in a new thread, not in this one.
3. **Name the chat and record it (D-157).** Run `chat <D-NNN>` for the stable name (`NOME DO CHAT: ...`). **Codex App:** when the thread tools are loaded and this chat is dedicated to the demand, call `codex_app.list_threads` to find the current thread id, then `codex_app.set_thread_title` with that name (search for the thread tools first if they are not loaded). When the chat already holds other demandas, do not rename it; use the name it already has. Either way record it with `chat <D-NNN> --title "<name>"` and show the name to the developer - the queue and `status --all` cite it so they can come back.
4. **Antigravity (no thread API):** nothing to rename programmatically — the printed line is enough.
5. If shell access fails, surface the exact command the developer can run by hand instead of silently failing.
6. **Recommend the model for this demand (D-153)** — when the demand is created or started in this chat: from what you read in the request and the code, run `triage <D-NNN> --scope <areas> [--risk auth|migration|concurrency|security|prod|data] [--uncertain] [--irreversible]` and show the `MODELO RECOMENDADO ...` line. If this chat runs on a different model, say so plainly - switching is the developer's call. A Fable suggestion is only a suggestion: ask before using it. The audit never runs below Opus.
7. **Record the model actually used (D-154)** — once per chat: `model <D-NNN> --who chat --model <haiku|sonnet|opus|fable> --purpose "<what this chat did>"`. When you delegate to a subagent, pick its model by what it does (locate/read code: haiku; a 1-2 file change: sonnet; review or audit: opus - never below) and record it the same way with `--who subagent`. Show the `MODELO USADO ...` line: the developer compares it with the recommendation (`model --summary`).

**Chats with an old name (D-194).** Lines `RENOMEIE O CHAT: <sessionId> -> <NOME DA DEMANDA>` (from `next`, `status`, `queue run` or `chat --pending`) name Claude Code sessions whose title fell behind the demand's stage. This host cannot rename them: show the lines to the developer and leave them pending - a Claude Code chat applies them and records `chat <D-NNN> --applied "<title>"`.
