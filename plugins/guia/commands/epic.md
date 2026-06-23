---
description: EPIC — create an `E-NNN` epic to orchestrate a large piece of work that breaks down into smaller stories (D-049). The epic itself does no implementation; it aggregates children. Use `feature/bug/chore "..." --under E-NNN` to attach a child story; `status E-NNN` prints the aggregated tree (closed/total children); `finish E-NNN` is REFUSED while any child is in a non-terminal status (Em desenvolvimento / Aguardando validacao / Planejada / Backlog / Bloqueada). No nested epics (2-level hierarchy only). `cancel` on an epic does NOT cascade: children remain as-is.
---

# Epic

Create an **Epic** (`E-NNN`) — an orchestrator for a large piece of work that breaks down into smaller **stories** (`D-NNN`). The epic itself does no implementation: it aggregates children and gates closure. This is the answer to "this demand is too big to fit in one chat" without losing rastreio.

The `title` is a short imperative phrase naming the whole effort ("Migrar X para Y", "Reformular fluxo de Z"). Use `--context "..."` to justify why this needed to be an epic and not a single demand.

**Run the engine.** It ships inside the plugin — no repo clone, no manual `init`. Invoke it through `${CLAUDE_PLUGIN_ROOT}` (the plugin install dir), never a path relative to the working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>      # bash (canonical — you call via the Bash tool)
python "$env:CLAUDE_PLUGIN_ROOT/bin/guia.py" <command>    # PowerShell
```

The engine roots itself at the current project and auto-creates `.guia/` there on the first command. Substitute `<command>` with the verb and arguments for this skill:

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

Reflect the printed `NOME DA DEMANDA` for the epic itself (`E-NNN ✨ - #DEV - <title>`). Stories get the standard demand-title format with their `D-NNN`. The chat is not renamed automatically — a chat-pai holds the epic and several stories, so the line is pure demand info, not a chat title.
