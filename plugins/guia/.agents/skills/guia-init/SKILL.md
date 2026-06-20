---
name: guia-init
description: SETUP — initialize Guia Fluxo in the CURRENT project: seed `.guia/` state and deploy the per-project lock config (`features/registry.yaml`, `features/lock-ignore.txt`) + `.githooks/commit-msg`, then set `git core.hooksPath`. Idempotent and never clobbers existing state. Options: `--no-locks` (seed `.guia/` only), `--force` (overwrite), `--project-name "<name>"`. Often optional — the engine auto-creates `.guia/` on the first task command; run `init` to opt into file locks. To create a demand use `feature`/`bug`/`chore`.
---

# Init

Set up Guia Fluxo in THIS project: seed the `.guia/` state and (by default) deploy the per-project lock config plus the `commit-msg` hook from the plugin, then point `git core.hooksPath` at `.githooks/`. Idempotent — existing state and templates are preserved, never overwritten.

Mostly optional: the engine auto-creates `.guia/` on the first task command, so you only need `init` to opt into file locks + the commit-msg guard. Run it once when adopting the pack in a new repo.

**Run the engine** via the repo wrapper (portable fallback on Linux/Mac/no PowerShell: `python core/src/guia.py <command>`):

```powershell
.\core\bin\guia.ps1 <command>
```

Substitute `<command>` with the verb and arguments for this skill:

```text
init
```

Useful flags:
- `--no-locks` — seed `.guia/` only; skip the lock registry, the `commit-msg` hook and `core.hooksPath`.
- `--force` — overwrite existing state/templates (destructive; rarely needed).
- `--project-name "<name>"` — override the project name (default: the directory name).

After it runs, tell the developer what was seeded vs preserved (the engine prints `+` for written and `=` for preserved files). If the lock config was deployed, remind them that editing a locked file now requires `[unlock:<id>] motivo: <razao>` in the commit message.
