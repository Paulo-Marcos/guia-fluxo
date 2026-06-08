# Feature

Create a new feature task before editing code.

{{include: _partials/title_context_rules.md}}

Run:

```powershell
.\core\bin\guia.ps1 feature "$ARGUMENTS"
```

Flags uteis:
- `--context "<why>"` — motivacao (sintetize como descrito acima).
- `--origin "<source>"` — origem alternativa (default: "Guia Fluxo (data)").
- `--status backlog|planned|in-development` — default `in-development`.

Portable fallback (Linux/Mac/sem PowerShell): `python core/src/guia.py feature "$ARGUMENTS"`.

{{include: _partials/post_cli.claude.md}}

{{include: _partials/lock_protocol.md}}

Then continue with the implementation.
