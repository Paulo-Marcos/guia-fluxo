# Ready Shim

**You (the agent) call this when implementation ends** — not the human. `ready` is the handoff to human validation; the human then validates in real use, and you call `finish` afterward. Do not skip `ready` and go straight to `finish`.

Call the core process script:

```powershell
.\core\bin\guia.ps1 ready F-000 --file path/to/file --summary "What changed" --validation "What passed"
```

Then continue using `guia-fluxo`.
