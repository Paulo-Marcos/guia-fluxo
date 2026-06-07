# Plan Shim

Marca task como `Planejada` (triada mas nao iniciada). Aceita transicao de `Backlog` ou `Em desenvolvimento`.

Call the core process script:

```powershell
.\core\bin\ai.ps1 plan D-NNN [--note "..."]
```

Falha em estado terminal ou ja `Planejada`. Use `$start` para sair de `Planejada` para `Em desenvolvimento`.

Depois continue usando `ai-process`.
