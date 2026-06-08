# Plan

**Marca a task como `Planejada`** (triada mas ainda nao iniciada). Use quando voce ja sabe que vai mexer naquela demanda mas nao agora — sai do `Backlog` (parqueado) ou volta do `Em desenvolvimento` (despriorizado).

Run:

```powershell
.\core\bin\guia.ps1 plan $ARGUMENTS [--note "Por que esta planejando agora"]
```

Distinto de:
- `$backlog add`: parquear ideia ainda nao triada.
- `$promote`: triar um B-NNN legacy avaliando feature/bug e ja comecar.
- `$start`: comecar agora (sai de `Backlog` ou `Planejada` para `Em desenvolvimento`).

Falha se a task esta em estado terminal (`Validada`, `Finalizada`, `Cancelada`) ou ja esta `Planejada`. Tasks que sobem de `Backlog` para `Planejada` aparecem em `FEATURES.md` (entram no catalogo).

Portable fallback (Linux/Mac/sem PowerShell): `python core/src/guia.py plan $ARGUMENTS`.

Depois repita o `NOME DO CHAT: ...` (vira `#PLANEJADA`) e rode `/rename <suggested-title>` se a sessao expor.
