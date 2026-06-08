# Chore Shim

Cria uma task de manutencao (refactor pequeno, build/lint, deps, config, docs sem mudanca de comportamento). Introduzido na Fase 4 do ADR-0011.

{{include: _partials/title_context_rules.md}}

Call the core process script:

```powershell
.\core\bin\guia.ps1 chore "<title>" --context "<o que + por que>"
```

Optional flags: `--status backlog|planned|in-development`, `--origin "<source>"`.

{{include: _partials/post_cli.agent.md}}

{{include: _partials/lock_protocol.md}}

Then continue with the maintenance work, following `guia-fluxo` for cross-cutting protocol.
