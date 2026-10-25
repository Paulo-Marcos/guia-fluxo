---
name: guia-epic
description: "EPIC — create an `E-NNN` epic to orchestrate a large piece of work that breaks down into smaller stories (D-049). The epic itself does no implementation; it aggregates children. Use `feature/bug/chore \"...\" --under E-NNN` to attach a child story; `status E-NNN` prints the aggregated tree (closed/total children); `finish E-NNN` is REFUSED while any child is in a non-terminal status (Em desenvolvimento / Aguardando validacao / Planejada / Backlog / Bloqueada). No nested epics (2-level hierarchy only). `cancel` on an epic does NOT cascade: children remain as-is."
---

# Epic

Create an **Epic** (`E-NNN`) — an orchestrator for a large piece of work that breaks down into smaller **stories** (`D-NNN`). The epic itself does no implementation: it aggregates children and gates closure. This is the answer to "this demand is too big to fit in one chat" without losing rastreio.

The `title` is a short imperative phrase naming the whole effort ("Migrar X para Y", "Reformular fluxo de Z"). Use `--context "..."` to justify why this needed to be an epic and not a single demand.

**Run the engine** via the repo wrapper (portable fallback on Linux/Mac/no PowerShell: `python core/src/guia.py <command>`):

```powershell
.\core\bin\guia.ps1 <command>
```

Substitute `<command>` with the verb and arguments for this skill:

```text
epic "Reformular fluxo X" --context "Por que isso virou epic"
feature "Tela Y" --under E-001            # cria D-NNN como filho de E-001
bug "Bug Z" --under E-001                 # tambem aceita
chore "Limpar legado W" --under E-001     # tambem
status E-001                              # arvore agregada (filhos + status)
finish E-001                              # SO fecha quando todos os filhos forem terminais
```

## Rules and guarantees

- **Own numbering.** Epics are `E-NNN`; stories are `D-NNN`. They never collide visually.
- **2-level hierarchy.** No nested epics. `--under` only accepts an Epic id; otherwise the command is refused.
- **`status E-NNN`** prints the tree with `Progresso: closed/total` and lists every child with its current status. If any child is open, prints the blockage notice.
- **`finish E-NNN`** is **refused** while any child is in a non-terminal status (`Em desenvolvimento`, `Aguardando validacao`, `Planejada`, `Backlog`, `Bloqueada`). Terminal statuses that count as "done for the epic": `Validada`, `Finalizada`, `Resolvida`, `Cancelada`.
- **`cancel E-NNN`** does **not** cascade to children. Cancelling the epic just terminates the parent; each child stays as-is and you decide caso a caso.
- **`parentId` is immutable.** To move a story between epics, cancel it and recreate under the new parent.

## When to use

- A demand that won't fit in one chat / one PR.
- A migration with several visible deliverables.
- A coordinated cross-area change (frontend + backend + docs) where each side has its own story.

## When NOT to use

- A single demand that just needs `--depends-on` to wait for another (use D-067, not D-049).
- A two-line refactor that doesn't deserve a chat-pai. Just use `chore`.

Reflect the printed `NOME DA DEMANDA` for the epic itself (`E-NNN ✨ - #DEV - <title>`) and name this chat after it (below). The epic's chat holds the epic alone (D-185): each story is created here with `--under E-NNN --status planned` and then runs in **its own linked chat** (`start_session`, titled with the story's `NOME DA DEMANDA`, brief starting with `start <D-NNN>`). Never `start` the stories in batch here: a story started in the epic's chat records no chat of its own, and the queue cannot rename it when it integrates (D-190). Come back to the epic's chat for `epic status` and the epic's `finish`.

**Name the chat and record it (D-157).** Run `chat <D-NNN>` for the stable name (`NOME DO CHAT: ...`). **Codex App:** when the thread tools are loaded and this chat is dedicated to the demand, call `codex_app.list_threads` to find the current thread id, then `codex_app.set_thread_title` with that name (search for the thread tools first if they are not loaded). When the chat already holds other demandas, do not rename it; use the name it already has. Either way record it with `chat <D-NNN> --title "<name>"` and show the name to the developer - the queue and `status --all` cite it so they can come back. A demand started from another demand's chat (an epic's story, a follow-up from the audit or the queue) is worked in a thread of its own, which records itself.

**Controller and executor threads (D-199, ADR-0023)** - when one thread takes the developer's requests and hands each demand to a thread of its own: the **controller** splits the request into demands through the engine, follows the queue, reconciles names and runs `finish` only on the developer's authorization; the **executor** does `start` through `ready` and `next` until `stop`/`done`, reporting back. Record the roles with `chat <D-NNN> --role executor --controller <controller thread id>` (or `--role controller` for a demand the controller works itself). Authorization (unlock, approve, autonomy, configure, queue control, `finish`) is the developer's and is forwarded quoting the developer's words; nobody grants it on their own, and nobody merges the PR.
