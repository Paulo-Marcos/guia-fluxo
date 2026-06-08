# Feature

Create a new feature task before editing code. Use when the human asks for a NEW capability (not a bug fix, not maintenance).

{{include: _partials/title_context_rules.md}}

Run:

```powershell
.\core\bin\guia.ps1 feature "<title>" --context "<context>"
```

Useful flags:
- `--context "<why>"` — motivation (synthesize per the rules above).
- `--origin "<source>"` — alternate origin (default: "Guia Fluxo (date)").
- `--status backlog|planned|in-development` — default `in-development`.

Portable fallback (Linux/Mac/no PowerShell): `python core/src/guia.py feature "<title>"`.

{{include_per_target: _partials/post_cli}}

{{include: _partials/lock_protocol.md}}

Then continue with the implementation.
