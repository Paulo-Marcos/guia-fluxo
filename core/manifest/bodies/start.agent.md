# Start Shim

Inicia trabalho em uma task `Planejada` ou `Backlog` (status -> `Em desenvolvimento`). Pressupoe triagem feita; se precisa decidir kind, use `$promote`.

Call the core process script:

```powershell
.\core\bin\guia.ps1 start D-NNN [--note "..."]
```

Falha se a task ja esta `Em desenvolvimento`, terminal ou `Bloqueada` (use `$unblock`).

Depois continue usando `guia-fluxo`.
