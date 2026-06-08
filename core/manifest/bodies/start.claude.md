# Start

**Comeca trabalho em uma task Planejada (ou diretamente do Backlog).** Move status para `Em desenvolvimento`. Pressupoe que a triagem (kind = feature/bug/chore) ja foi feita — se ainda precisa decidir o tipo, use `$promote`.

Run:

```powershell
.\core\bin\guia.ps1 start $ARGUMENTS [--note "Comecando agora porque..."]
```

Distinto de:
- `$promote <B-NNN>`: triar item de backlog avaliando kind e plano antes de comecar.
- `$plan`: marcar como triada sem iniciar.
- `$feature/$issue` (novos): criar task do zero ja `Em desenvolvimento`.

Aceita transicao de `Backlog` (atalho que pula `Planejada`) ou `Planejada`. Falha se a task ja esta `Em desenvolvimento`, em estado terminal (`Validada`, `Finalizada`, `Cancelada`) ou `Bloqueada` (use `$unblock`).

Tasks que sobem de `Backlog` entram em `FEATURES.md`.

Portable fallback (Linux/Mac/sem PowerShell): `python core/src/guia.py start $ARGUMENTS`.

Depois repita o `NOME DO CHAT: ...` (vira `#DEV`) e rode `/rename <suggested-title>` se a sessao expor.
