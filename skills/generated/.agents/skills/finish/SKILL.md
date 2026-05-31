---
name: finish
description: Shim for ai-process. Use when the user invokes $finish or asks to finalize/close a validated feature or issue, commit it, and optionally lock it.
---

# Finish Shim

Call the core process script:

```powershell
.\scripts\ai.ps1 finish F-000 --lock --lock-id feature-slug
```

`finish` means the developer already validated the work. It suggests `#FINALIZADO` and commits by default. Use `--no-commit` for dry close.
