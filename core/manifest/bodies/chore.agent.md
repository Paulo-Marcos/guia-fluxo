# Chore Shim

Cria uma task de manutencao (refactor pequeno, build/lint, deps, config, docs sem mudanca de comportamento). Introduzido na Fase 4 do ADR-0011.

Call the core process script:

```powershell
.\core\bin\guia.ps1 chore "<title>" --context "<o que + por que>"
```

Aceita `--status backlog|planned|in-development`.

Then continue using `guia-fluxo`.
