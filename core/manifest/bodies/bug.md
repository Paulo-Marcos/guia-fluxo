# Bug

Create a bug task before editing code. Use for a regression, a defect, or any incorrect behavior that needs investigation and fix.

{{include: _partials/title_context_rules.md}}

Run:

```powershell
.\core\bin\guia.ps1 bug "<title>" --context "<observed symptom + impact>"
```

Useful flags:
- `--context "<symptom + impact>"` — observed behavior vs expected, who is affected.
- `--status backlog|planned|in-development` (default `in-development`) — `backlog` if not triaged, `planned` if planned but not now.
- `--origin "<source>"` — alternate origin.

Portable fallback (Linux/Mac/no PowerShell): `python core/src/guia.py bug "<title>"`.

{{include_per_target: _partials/post_cli}}

{{include: _partials/lock_protocol.md}}

Then continue with the investigation and fix.
