# Start

**Start work on a Planejada task (or directly from the Backlog).** Moves status to `Em desenvolvimento`. Assumes triage (kind = feature/bug/chore) is done — if you still need to decide the kind, use `$promote`.

{{include_per_target: _partials/run_cmd}}

```text
start <D-NNN> [--note "Starting now because..."]
```

Distinct from:
- `$promote <B-NNN>`: triage a backlog item deciding kind and plan before starting.
- `$plan`: mark as triaged without starting.
- `$feature/$bug/$chore` (new tasks): create a fresh task already `Em desenvolvimento`.

Accepts transition from `Backlog` (shortcut that skips `Planejada`) or `Planejada`. Fails if the task is already `Em desenvolvimento`, in a terminal state (`Validada`, `Finalizada`, `Cancelada`), or `Bloqueada` (use `$unblock`).

Tasks promoted from `Backlog` enter `.guia/DEMANDAS.md`.

{{include_per_target: _partials/post_cli}}
