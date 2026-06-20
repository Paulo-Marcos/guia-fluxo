# Init

Set up Guia Fluxo in THIS project: seed the `.guia/` state and (by default) deploy the per-project lock config plus the `commit-msg` hook from the plugin, then point `git core.hooksPath` at `.githooks/`. Idempotent — existing state and templates are preserved, never overwritten.

Mostly optional: the engine auto-creates `.guia/` on the first task command, so you only need `init` to opt into file locks + the commit-msg guard. Run it once when adopting the pack in a new repo.

{{include_per_target: _partials/run_cmd}}

```text
init
```

Useful flags:
- `--no-locks` — seed `.guia/` only; skip the lock registry, the `commit-msg` hook and `core.hooksPath`.
- `--force` — overwrite existing state/templates (destructive; rarely needed).
- `--project-name "<name>"` — override the project name (default: the directory name).

After it runs, tell the developer what was seeded vs preserved (the engine prints `+` for written and `=` for preserved files). If the lock config was deployed, remind them that editing a locked file now requires `[unlock:<id>] motivo: <razao>` in the commit message.
