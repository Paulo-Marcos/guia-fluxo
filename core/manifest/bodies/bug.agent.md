# Bug Shim

Cria uma task de bug. Substitui o antigo `issue` (removido na Fase 4 do ADR-0011).

Call the core process script:

```powershell
.\core\bin\guia.ps1 bug "<title>" --context "<sintoma + impacto>"
```

Aceita tambem `--status backlog|planned|in-development` para criar ja parqueado ou ja triado.

Then continue using `guia-fluxo`.
