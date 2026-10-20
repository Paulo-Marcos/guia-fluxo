# Status

Show the current Guia Fluxo task and the suggested chat title. Read-only — never mutates state.

{{include_per_target: _partials/run_cmd}}

```text
status            # current task
status <D-NNN>    # a specific task
status <D-NNN> --json   # raw task JSON, for scripts
```

The default output is readable: header (stage, kind, model, branch, PR, chat), then context, plan, files, summary, validations, pending, Request -> Test and the steps the demand went through. A `Planejada`/`Em desenvolvimento` demand without a plan gets a warning - record one with `plan <D-NNN> --step "..."`.

{{include_per_target: _partials/post_cli}}
