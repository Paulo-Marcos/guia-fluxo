# Ready Shim

**You (the agent) call this when implementation ends** — not the human. `ready` is the handoff to human validation; the human then validates in real use, and you call `finish` afterward. Do not skip `ready` and go straight to `finish` — that bypasses the human-in-the-loop gate (the reason `validate` was deprecated in F-003).

Call the core process script:

```powershell
.\core\bin\guia.ps1 ready D-000 --file path/to/file --summary "What changed" --validation "What passed"
```

Pass changed files with `--file`, implementation notes with `--summary`, validation commands run with `--validation`, and manual gaps still pending with `--pending`.

{{include: _partials/post_cli.agent.md}}

Then **stop and wait** for the developer to validate. Do not run `finish` until the developer confirms validation in real use.
