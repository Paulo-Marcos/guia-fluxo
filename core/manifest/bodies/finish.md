# Finish

Close an already-validated task. Run **only after** the developer confirms validation in real use — `finish` is the closing gate, not a shortcut.

> **`finish` is the USER's action (behavioral rule, D-098).** Closing is the developer's call. **If you are an AI agent, run `finish` ONLY when the developer requests `/guia:finish` or explicitly authorizes it — NEVER on your own initiative.** Your default job ends at `ready`: hand off and wait for the developer to ask for the close. This is a behavioral rule, not a CLI parameter — there is no env var or flag to set (D-098 removed the `GUIA_HUMAN_FINISH` env gate the earlier D-080 had tried; sending a variable was bad, and the engine cannot tell an agent apart from a human anyway).

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

Run this **only** because the developer asked for it (no env var or flag — see the rule above):

```text
finish <D-NNN> --docs-touched docs/reference/cli.md --docs-touched CHANGELOG.md
# or, when nothing needed touching:
finish <D-NNN> --docs-skip "internal flow, no user-facing change"
```

`finish` commits by default. Use `--no-commit` for dry close. Lock with `--lock --lock-id feature-slug --lock-description "..."` only when the developer asks for it.

{{include_per_target: _partials/post_cli}}

{{include: _partials/lock_protocol.md}}

Task is closed.
