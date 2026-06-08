# Feature Shim

Use when the human asks for a NEW capability (not a bug fix, not maintenance). Creates a `D-NNN` feature task and starts implementation.

{{include: _partials/title_context_rules.md}}

Call the core process script:

```powershell
.\core\bin\guia.ps1 feature "<title>" --context "<context>"
```

Optional flags: `--status backlog|planned|in-development` (default `in-development`), `--origin "<source>"`.

{{include: _partials/post_cli.agent.md}}

{{include: _partials/lock_protocol.md}}

Then continue with the implementation, following `guia-fluxo` for cross-cutting protocol.
