# Bug

Cria uma task de bug (regressao, defeito, comportamento incorreto) antes de editar codigo. Substitui o antigo `/issue` (removido na Fase 4 do ADR-0011 — `issue` colidia com o sentido guarda-chuva do termo em GitHub/Jira/Linear).

{{include: _partials/title_context_rules.md}}

Run:

```powershell
.\core\bin\guia.ps1 bug "$ARGUMENTS"
```

Flags uteis:
- `--context "<sintoma + impacto>"` — comportamento observado vs esperado, quem foi atingido.
- `--status backlog|planned|in-development` (default `in-development`) — `backlog` se ainda nao triado, `planned` se ja sabe que vai mexer mas nao agora.
- `--origin "<source>"` — origem alternativa.

Portable fallback (Linux/Mac/sem PowerShell): `python core/src/guia.py bug "$ARGUMENTS"`.

{{include: _partials/post_cli.claude.md}}

{{include: _partials/lock_protocol.md}}

Then continue with the investigation and fix.
