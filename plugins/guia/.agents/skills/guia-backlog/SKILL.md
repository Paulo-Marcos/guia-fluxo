---
name: guia-backlog
description: "DEFER-AND-PARK skill — never starts implementation. Subcommands: `add <title> --context \"<why>\"` parks an idea (saved to `.guia/tasks.json` with `status=Backlog`); `list` shows all parked items; `promote <id>` delegates to the promote flow. To start work immediately use `feature`/`bug`/`chore`; to evaluate one parked item before converting use `promote`."
---

# Backlog

Manage parked work without starting implementation. `backlog add` creates a `D-NNN` task with `status=Backlog`. `backlog list` shows all parked items. `backlog promote` delegates to the `/promote` flow.

## Title vs Context

When the human asks in loose phrasing, **synthesize** — do not pass the raw sentence to the CLI.

- `<title>`: short imperative, 5–8 words, ≤60 chars. Captures the *what*. Title is what shows in `NOME DA DEMANDA` and in task lists.
- `<context>`: full motivation, scenario, success criteria. Captures the *why*. Multi-line allowed. Goes into `task.context`, `.guia/DEMANDAS.md`, and search.

Example:

> Human: "queria que o /finish mostrasse o tempo total da task"
>
> → title:   `Show total task time on /finish`
> → context: `User wants /finish to print elapsed time since task creation so they can see how long the work took without opening JSON.`

If the human-provided phrasing already reads as an imperative under 60 chars, use it as-is. Synthesis is for loose/long phrasings, not a mandatory rewrite.

**Run the engine** via the repo wrapper (portable fallback on Linux/Mac/no PowerShell: `python core/src/guia.py <command>`):

```powershell
.\core\bin\guia.ps1 <command>
```

Substitute `<command>` with the verb and arguments for this skill:

```text
backlog add "<title>" --context "<context>"    # if the user provided a title
backlog list                                   # show parked work
backlog promote B-001                          # promote a backlog item
```

## After running the script

1. Read `.guia/current-task.json` to confirm the new state.
2. Repeat the exact `NOME DA DEMANDA: ...` line printed by the script — do not paraphrase or translate it. It names the **current demand**. One demand per chat (D-185): a demand that comes up while working another (an epic story, a follow-up, a bug found on the way) is created with the CLI and worked in a new thread, not in this one.
3. **Name the chat and record it** - the block below this list (D-157).
4. **Antigravity (no thread API):** nothing to rename programmatically — the printed line is enough.
5. If shell access fails, surface the exact command the developer can run by hand instead of silently failing.
6. **Recommend the model for this demand (D-153)** — when the demand is created or started in this chat: from what you read in the request and the code, run `triage <D-NNN> --scope <areas> [--risk auth|migration|concurrency|security|prod|data] [--uncertain] [--irreversible]` and show the `MODELO RECOMENDADO ...` line. If this chat runs on a different model, say so plainly - switching is the developer's call. A Fable suggestion is only a suggestion: ask before using it. The audit never runs below Opus.
7. **Record the model actually used (D-154)** — once per chat: `model <D-NNN> --who chat --model <haiku|sonnet|opus|fable> --purpose "<what this chat did>"`. When you delegate to a subagent, pick its model by what it does (locate/read code: haiku; a 1-2 file change: sonnet; review or audit: opus - never below) and record it the same way with `--who subagent`. Show the `MODELO USADO ...` line: the developer compares it with the recommendation (`model --summary`).

**Chats with an old name (D-194).** Lines `RENOMEIE O CHAT: <sessionId> -> <NOME DA DEMANDA>` (from `next`, `status`, `queue run` or `chat --pending`) name Claude Code sessions whose title fell behind the demand's stage. This host cannot rename them: show the lines to the developer and leave them pending - a Claude Code chat applies them and records `chat <D-NNN> --applied "<title>"`.

**Name the chat and record it (D-157).** Run `chat <D-NNN>` for the stable name (`NOME DO CHAT: ...`). **Codex App:** when the thread tools are loaded and this chat is dedicated to the demand, call `codex_app.list_threads` to find the current thread id, then `codex_app.set_thread_title` with that name (search for the thread tools first if they are not loaded). When the chat already holds other demandas, do not rename it; use the name it already has. Either way record it with `chat <D-NNN> --title "<name>"` and show the name to the developer - the queue and `status --all` cite it so they can come back. A demand started from another demand's chat (an epic's story, a follow-up from the audit or the queue) is worked in a thread of its own, which records itself.

**Controller and executor threads (D-199, ADR-0023)** - when one thread takes the developer's requests and hands each demand to a thread of its own: the **controller** splits the request into demands through the engine, follows the queue, reconciles names and runs `finish` only on the developer's authorization; the **executor** does `start` through `ready` and `next` until `stop`/`done`, reporting back. Record the roles with `chat <D-NNN> --role executor --controller <controller thread id>` (or `--role controller` for a demand the controller works itself). Authorization (unlock, approve, autonomy, configure, queue control, `finish`) is the developer's and is forwarded quoting the developer's words; nobody grants it on their own, and nobody merges the PR. **D-210 (ADR-0025):** the executor never opens a thread for a follow-up - it creates it with `--status planned --from <its D-NNN>` and the controller decides; questions to the developer go through `ask <D-NNN> "<question>" --option ...`, the controller sees them all in `guia controle` (executors, stage, PR, who holds the ball, proposals, threads to archive, free slots up to `controller.maxExecutors`) and records the developer's words with `answer <D-NNN> P<n> --quote "..."`; finished threads are archived only with the developer's ok, then `chat <D-NNN> --archived`.

**Do not start implementation.** Backlog parks work for later. To begin work on a parked item, use `/promote <B-NNN>` (evaluation + plan) or `/start <D-NNN>` (already triaged).
