# Unblock Shim

Retoma uma task pausada (`Bloqueada` -> `Em desenvolvimento`).

Call the core process script:

```powershell
.\core\bin\guia.ps1 unblock F-000 [--note "O que destravou"]
```

Falha se a task nao estava em `Bloqueada`.

Depois continue usando `guia-fluxo`.
