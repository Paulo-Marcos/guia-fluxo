# Unblock

**Retoma uma task pausada.** Move o status de `Bloqueada` para `Em desenvolvimento`. Use depois de `block` quando a dependencia/decisao que travava saiu do caminho.

Run:

```powershell
.\core\bin\guia.ps1 unblock $ARGUMENTS [--note "O que destravou"]
```

`--note` e opcional - usado quando vale registrar o que destravou (decisao tomada, dependencia resolvida).

Falha se a task nao estava em `Bloqueada` (preserva estados de fluxo).

Portable fallback (Linux/Mac/sem PowerShell): `python core/src/guia.py unblock $ARGUMENTS`.

Depois repita a linha `NOME DO CHAT: ...` (volta para `#DEV`) e rode `/rename <suggested-title>` se a sessao expor essa API.
