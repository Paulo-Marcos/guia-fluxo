---
name: finish
description: CLOSE an ALREADY-validated task; commits by default and optionally creates a lock. Triggered by /finish or "$finish" / "finalizar / fechar / concluir tarefa validada". Use ONLY after the developer explicitly confirms the work is final — never as a shortcut to skip validation. Do NOT use for: sending the task to validation first (use $ready), or showing current state without closing (use $status).
---

# Finish Shim

Call the core process script:

```powershell
.\scripts\ai.ps1 finish F-000 --lock --lock-id feature-slug
```

`finish` means the developer already validated the work. It suggests `#FINALIZADO` and commits by default. Use `--no-commit` for dry close.
