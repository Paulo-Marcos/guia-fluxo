# Bug

Cria uma task de bug (regressao, defeito, comportamento incorreto) antes de editar codigo. Substitui o antigo `/issue` (removido na Fase 4 do ADR-0011 — `issue` colidia com o sentido guarda-chuva do termo em GitHub/Jira/Linear).

Run:

```powershell
.\core\bin\ai.ps1 bug "$ARGUMENTS"
```

Flags uteis:
- `--context "<sintoma + impacto>"` — comportamento observado vs esperado, quem foi atingido.
- `--status backlog|planned|in-development` (default `in-development`) — usar `backlog` se ainda nao for triado, `planned` se ja sabe que vai mexer mas nao agora.
- `--origin "<source>"` — origem alternativa (rota padrao: "AI process (data)").

Portable fallback (Linux/Mac/sem PowerShell): `python core/src/ai.py bug "$ARGUMENTS"`.

Depois leia `.ai/current-task.json`, repita o `NOME DO CHAT: ...` (vira `D-NNN 🐛 - #DEV - ...`), rode `/rename <suggested-title>` se a sessao suportar, e siga para a investigacao + correcao.
