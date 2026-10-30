---
name: guia-worktree
description: "WORKTREE — `worktree add D-NNN` creates the demand's isolated worktree and branch (`d-NNN-<slug>`, following the PR branch from origin when one exists); `worktree remove D-NNN [--force]` removes it safely (junctions undone first). Options: `--path`, `--branch`. Run from the main tree."
---

# Worktree

**Run the engine** via the repo wrapper (portable fallback on Linux/Mac/no PowerShell: `python core/src/guia.py <command>`):

```powershell
.\core\bin\guia.ps1 <command>
```

Substitute `<command>` with the verb and arguments for this skill:

```text
worktree add D-NNN
worktree remove D-NNN
```

- State stays in the main tree; commands run inside the worktree resolve the demand by branch.
- The worktree is where the demand's chat works: when this chat is that chat, it also carries the demand's name and session (below) - `worktree add` does not replace that step.

**Name the chat and record it (D-157).** Run `chat <D-NNN>` for the stable name (`NOME DO CHAT: ...`). **Codex App:** when the thread tools are loaded and this chat is dedicated to the demand, call `codex_app.list_threads` to find the current thread id, then `codex_app.set_thread_title` with that name (search for the thread tools first if they are not loaded). When the chat already holds other demandas, do not rename it; use the name it already has. Either way record it with `chat <D-NNN> --title "<name>"` and show the name to the developer - the queue and `status --all` cite it so they can come back. A demand started from another demand's chat (an epic's story, a follow-up from the audit or the queue) is worked in a thread of its own, which records itself.

**Controller and executor threads (D-199, ADR-0023)** - when one thread takes the developer's requests and hands each demand to a thread of its own: the **controller** splits the request into demands through the engine, follows the queue, reconciles names and runs `finish` only on the developer's authorization; the **executor** does `start` through `ready` and `next` until `stop`/`done`, reporting back. Record the roles with `chat <D-NNN> --role executor --controller <controller thread id>` (or `--role controller` for a demand the controller works itself). Authorization (unlock, approve, autonomy, configure, queue control, `finish`) is the developer's and is forwarded quoting the developer's words; nobody grants it on their own, and nobody merges the PR. **D-210 (ADR-0025):** the executor never opens a thread for a follow-up - it creates it with `--status planned --from <its D-NNN>` and the controller decides; questions to the developer go through `ask <D-NNN> "<question>" --option ...`, the controller sees them all in `guia controle` (executors, stage, PR, who holds the ball, proposals, threads to archive, free slots up to `controller.maxExecutors`) and records the developer's words with `answer <D-NNN> P<n> --quote "..."`; finished threads are archived only with the developer's ok, then `chat <D-NNN> --archived`.
