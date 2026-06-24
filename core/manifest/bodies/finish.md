# Finish

Close an already-validated task. Run **only after** the developer confirms validation in real use — `finish` is the closing gate, not a shortcut.

> **Human authorization required (technical gate, D-080).** `finish` is the developer's call. The tool now **refuses** to close unless the developer pre-authorized it via the `GUIA_HUMAN_FINISH=1` env var set in their session. **If you are an AI agent, your job ends at `ready` — do NOT set this env var yourself; it is the developer's signal.** When the developer has already given prior authorization (the env is set in the session), `finish` may run; otherwise stop at `ready` and hand off.

{{include_per_target: _partials/run_cmd}}

## 1) Docs hook (mandatory when `.guia/docs-map.yaml` exists)

Run the docs check before closing:

```text
docs-check
```

For each listed candidate:
- Open the file and decide if this task changes anything relevant to it.
- Update what makes sense (README pointer, CLI reference entry, CHANGELOG entry, ADR, explanation paragraph).
- Note the paths you touched.

If the project has no `.guia/docs-map.yaml`, the hook is a no-op and `finish` runs as before.

## 2) Close

Requires the developer's prior authorization — the `GUIA_HUMAN_FINISH=1` env var set in the session (D-080), e.g. `$env:GUIA_HUMAN_FINISH = "1"` in PowerShell:

```text
finish <D-NNN> --docs-touched docs/reference/cli.md --docs-touched CHANGELOG.md
# or, when nothing needed touching:
finish <D-NNN> --docs-skip "internal flow, no user-facing change"
```

`finish` commits by default. Use `--no-commit` for dry close. Lock with `--lock --lock-id feature-slug --lock-description "..."` only when the developer asks for it.

{{include_per_target: _partials/post_cli}}

{{include: _partials/lock_protocol.md}}

Task is closed.
