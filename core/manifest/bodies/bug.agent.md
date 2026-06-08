# Bug Shim

Cria uma task de bug (regressao, defeito, comportamento incorreto). Substitui o antigo `issue` (removido na Fase 4 do ADR-0011).

{{include: _partials/title_context_rules.md}}

Call the core process script:

```powershell
.\core\bin\guia.ps1 bug "<title>" --context "<sintoma + impacto>"
```

Optional flags: `--status backlog|planned|in-development` (default `in-development`), `--origin "<source>"`.

{{include: _partials/post_cli.agent.md}}

{{include: _partials/lock_protocol.md}}

Then continue with investigation and fix, following `guia-fluxo` for cross-cutting protocol.
