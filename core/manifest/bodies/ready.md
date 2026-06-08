# Ready

**The agent (you) calls this when implementation ends** — not the human. `ready` is the handoff to human validation; the human then validates in real use, and you call `finish` afterward. Do not skip `ready` and go straight to `finish` — that bypasses the human-in-the-loop gate (the reason `validate` was deprecated in F-003).

Run:

```powershell
.\core\bin\guia.ps1 ready <D-NNN> --file path/to/file --summary "What changed" --validation "What passed"
```

Pass changed files with `--file`, implementation notes with `--summary`, validation commands run with `--validation`, and manual gaps still pending with `--pending`.

Portable fallback (Linux/Mac/no PowerShell): `python core/src/guia.py ready <D-NNN> ...`.

{{include_per_target: _partials/post_cli}}

Then **stop and wait** for the developer to validate. Do not run `finish` until the developer confirms validation in real use.
