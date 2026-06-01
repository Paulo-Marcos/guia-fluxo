---
name: finish
description: CLOSE an ALREADY-validated task; runs the docs-check hook, commits by default and optionally creates a lock. Triggered by /finish or "$finish" / "finalizar / fechar / concluir tarefa validada". Use ONLY after the developer explicitly confirms the work is final — never as a shortcut to skip validation. Do NOT use for: sending the task to validation first (use $ready), or showing current state without closing (use $status).
---

# Finish Shim

Before closing, run the docs hook so this project's living docs stay current:

```powershell
.\scripts\ai.ps1 docs-check
```

For each listed candidate, open the doc, decide if it needs an update, edit it when it does. If `.ai/docs-map.yaml` does not exist the project has no docs control and the hook is a no-op.

Then close the task:

```powershell
.\scripts\ai.ps1 finish F-000 --docs-touched docs/reference/cli.md --docs-touched CHANGELOG.md
# or, when nothing needed touching:
.\scripts\ai.ps1 finish F-000 --docs-skip "fluxo interno, sem mudanca user-facing"
```

`finish` means the developer already validated the work. It suggests `#FINALIZADO` and commits by default. Use `--no-commit` for dry close. Lock with `--lock --lock-id feature-slug` when asked.
