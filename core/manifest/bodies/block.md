# Block

**Pause the current task with a mandatory reason.** Moves status to `Bloqueada`, preserves the WIP, and keeps the entry in `FEATURES.md`. Use to stop temporarily: external dependency, waiting on a decision, priority swap. Distinct from `cancel` (terminal, does not return) and `finish` (validated and closed).

Run:

```powershell
.\core\bin\guia.ps1 block <D-NNN> --reason "Why pausing"
```

`--reason` is **required** (recorded in `task.blocks[]` for blocked-time auditing).

Fails if the task is already in a terminal state (`Validada`, `Finalizada`, `Cancelada`) or already in `Bloqueada`.

To resume: `.\core\bin\guia.ps1 unblock <D-NNN>`.

Portable fallback (Linux/Mac/no PowerShell): `python core/src/guia.py block <D-NNN> --reason "..."`.

{{include_per_target: _partials/post_cli}}
