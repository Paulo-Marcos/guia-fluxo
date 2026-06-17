# Cancel

**Trigger by you (the agent) or the user, when the task will NOT be completed.** Marks the task as `Cancelada` (terminal) with a mandatory reason. Distinct from `block` (pause, will resume) and `finish` (validated and closed).

Typical cases:
- Demanda criada por engano.
- `promote` errado de um item de backlog.
- Mudanca de escopo: o que parecia uma feature/bug nao se justifica mais.

{{include_per_target: _partials/run_cmd}}

```text
cancel <D-NNN> --reason "Motivo curto"
```

`--reason` is **required** (justification stays in history under `task.cancellations[]` and in `FEATURES.md`).

Useful flags:
- `--keep-worktree`: do not remove the associated worktree (default: remove if present).
- `--set-current`: keep the task as current after canceling (default: clear `.guia/current-task.json` if the canceled task was current).

Fails if the task is already in a terminal state (`Validada`, `Finalizada`, `Cancelada`).

{{include_per_target: _partials/post_cli}}
