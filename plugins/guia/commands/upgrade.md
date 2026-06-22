---
description: MIGRATE — bring an existing project to the current Guia Fluxo layout: move `FEATURES.md` (root) → `.guia/DEMANDAS.md`, `features/registry.yaml` → `.guia/locks/registry.yaml`, `features/lock-ignore.txt` → `.guia/locks/lock-ignore.txt`, and drop `features/` if empty. Uses `git mv` to preserve history when the file is tracked. Idempotent: prints "Layout ja esta atualizado" when there's nothing to do. Options: `--dry-run` lists the plan without mutating. Refuses (exit 1) if any destination already exists — fix by hand. Distinct from `init` (sets up a virgin project), from `/plugin update` (updates the plugin itself), and from `backlog migrate` (legacy `B-NNN` items).
---

# Upgrade

Migrate an existing project from the **old layout** to the **current layout** of Guia Fluxo. Idempotent: nothing to move means nothing happens.

The old layout (pre-D-055/D-056) put process files at the project root:
- `FEATURES.md` (root) → moves to `.guia/DEMANDAS.md` (catalog now lives under `.guia/`, renamed because it holds feature/bug/chore = "demands", not only features).
- `features/registry.yaml` → moves to `.guia/locks/registry.yaml` (lock config now under `.guia/locks/`, honest name).
- `features/lock-ignore.txt` → moves to `.guia/locks/lock-ignore.txt`.
- `features/` is removed if it ends up empty.

When the file is tracked by git and you're inside a git repo, `git mv` is used so the rename history is preserved.

**Run the engine.** It ships inside the plugin — no repo clone, no manual `init`. Invoke it through `${CLAUDE_PLUGIN_ROOT}` (the plugin install dir), never a path relative to the working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/bin/guia.py" <command>      # bash (canonical — you call via the Bash tool)
python "$env:CLAUDE_PLUGIN_ROOT/bin/guia.py" <command>    # PowerShell
```

The engine roots itself at the current project and auto-creates `.guia/` there on the first command. Substitute `<command>` with the verb and arguments for this skill:

```text
upgrade --dry-run   # list the plan, don't mutate
upgrade             # apply
```

What to expect:
- **Nothing to migrate** → prints `Layout ja esta atualizado. Nada a migrar.` (exit 0). Safe to run repeatedly.
- **Conflict** (a destination already exists, e.g. someone already created `.guia/DEMANDAS.md` by another route) → exits 1 with `destino ja existe; resolva a mao` for each conflicting move. Nothing is mutated; resolve by hand and re-run.
- **Plan + apply** → prints `Plano de migracao:` followed by `moved <src> -> <dst>` per file and a final `Migracao concluida: N arquivo(s) movido(s).`

Distinct from:
- `init` — sets up a **virgin** project (seeds `.guia/`, deploys lock config). `upgrade` migrates an **existing** project that was set up with the old layout.
- `/plugin update guia@guia-fluxo` — updates the plugin code itself.
- `backlog migrate` — moves legacy `B-NNN` backlog items into `tasks.json`, unrelated to file layout.

After it runs, tell the developer which files were moved and remind them to commit (one commit, mostly rename = `git log --follow` keeps working).
