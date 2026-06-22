# Upgrade

Migrate an existing project from the **old layout** to the **current layout** of Guia Fluxo. Idempotent: nothing to move means nothing happens.

The old layout (pre-D-055/D-056) put process files at the project root:
- `FEATURES.md` (root) → moves to `.guia/DEMANDAS.md` (catalog now lives under `.guia/`, renamed because it holds feature/bug/chore = "demands", not only features).
- `features/registry.yaml` → moves to `.guia/locks/registry.yaml` (lock config now under `.guia/locks/`, honest name).
- `features/lock-ignore.txt` → moves to `.guia/locks/lock-ignore.txt`.
- `features/` is removed if it ends up empty.

When the file is tracked by git and you're inside a git repo, `git mv` is used so the rename history is preserved.

{{include_per_target: _partials/run_cmd}}

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
