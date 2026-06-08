# Finish Shim

Close an already-validated task. Run **only after** the developer confirms validation in real use — `finish` is the closing gate, not a shortcut.

## 1) Docs hook (mandatory when `.guia/docs-map.yaml` exists)

Run the docs check before closing:

```powershell
.\core\bin\guia.ps1 docs-check
```

For each listed candidate, open the doc, decide if it needs an update, edit it when it does. If `.guia/docs-map.yaml` does not exist the project has no docs control and the hook is a no-op.

## 2) Close

```powershell
.\core\bin\guia.ps1 finish D-000 --docs-touched docs/reference/cli.md --docs-touched CHANGELOG.md
# or, when nothing needed touching:
.\core\bin\guia.ps1 finish D-000 --docs-skip "fluxo interno, sem mudanca user-facing"
```

`finish` commits by default. Use `--no-commit` for dry close. Lock with `--lock --lock-id feature-slug --lock-description "..."` only when the developer asks for it.

{{include: _partials/post_cli.agent.md}}

{{include: _partials/lock_protocol.md}}

Task is closed. Continue using `guia-fluxo` only if the developer starts another task in this same conversation.
