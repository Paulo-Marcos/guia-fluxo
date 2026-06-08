# Finish Shim

Before closing, run the docs hook so this project's living docs stay current:

```powershell
.\core\bin\guia.ps1 docs-check
```

For each listed candidate, open the doc, decide if it needs an update, edit it when it does. If `.guia/docs-map.yaml` does not exist the project has no docs control and the hook is a no-op.

Then close the task:

```powershell
.\core\bin\guia.ps1 finish F-000 --docs-touched docs/reference/cli.md --docs-touched CHANGELOG.md
# or, when nothing needed touching:
.\core\bin\guia.ps1 finish F-000 --docs-skip "fluxo interno, sem mudanca user-facing"
```

`finish` means the developer already validated the work. It suggests `#FINALIZADO` and commits by default. Use `--no-commit` for dry close. Lock with `--lock --lock-id feature-slug --lock-description "..."` when asked.

Then continue using `guia-fluxo`.
