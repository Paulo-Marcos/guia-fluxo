# Status

Show the current Guia Fluxo task and the suggested chat title. Read-only — never mutates state.

Run:

```powershell
.\core\bin\guia.ps1 status
```

Or pass a specific task id:

```powershell
.\core\bin\guia.ps1 status <D-NNN>
```

Portable fallback (Linux/Mac/no PowerShell): `python core/src/guia.py status [<D-NNN>]`.

{{include_per_target: _partials/post_cli}}
