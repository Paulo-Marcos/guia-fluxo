# Plan

**Mark the task as `Planejada`** (triaged but not yet started). Use when you already know you will work on the task but not now — moves out of `Backlog` (parked) or back from `Em desenvolvimento` (deprioritized).

Run:

```powershell
.\core\bin\guia.ps1 plan <D-NNN> [--note "Why planning now"]
```

Distinct from:
- `$backlog add`: park an idea that has not been triaged yet.
- `$promote`: triage a backlog item, deciding kind and plan, then start immediately.
- `$start`: start now (moves from `Backlog` or `Planejada` to `Em desenvolvimento`).

Fails if the task is in a terminal state (`Validada`, `Finalizada`, `Cancelada`) or already `Planejada`. Tasks promoted from `Backlog` to `Planejada` enter `FEATURES.md` (join the catalog).

Portable fallback (Linux/Mac/no PowerShell): `python core/src/guia.py plan <D-NNN>`.

{{include_per_target: _partials/post_cli}}
