# Unblock

**Resume a paused task.** Moves status from `Bloqueada` back to `Em desenvolvimento`. Use after `block` once the dependency/decision blocking the work has been resolved.

Run:

```powershell
.\core\bin\guia.ps1 unblock <D-NNN> [--note "What unblocked it"]
```

`--note` is optional — useful when it is worth recording what unblocked it (decision made, dependency resolved).

Fails if the task was not in `Bloqueada` (preserves the flow states).

Portable fallback (Linux/Mac/no PowerShell): `python core/src/guia.py unblock <D-NNN>`.

{{include_per_target: _partials/post_cli}}
