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

## 2) Quality gate — run quality skills over what changed (D-095)

`finish` does **not** just run the test commands; it forces a **consultative quality validation** of the work. When product files changed (anything outside `.guia/`), the tool refuses to close until you confirm you ran it. **You (the agent) run the skills — the core only signals and enforces.**

Before closing:

1. Read `modifiedFiles` (the changed product files for this task).
2. Invoke the available **quality skills** — both **project** and **global** — over those files. Candidates in this environment:
   - `clean-code-review` (micro: readability, names, function size, smells)
   - `clean-architecture-guardian` (macro: layers, SOLID, SRP, coupling)
   - `tdd-dotnet` (tests/coverage of what changed)
   - `valida-pasta` (D-085, folder quality score 0–10, when available)
3. Evaluate every dimension: **(a)** code quality, **(b)** function/file size, **(c)** single responsibility (SRP), **(d)** coverage/tests, **(e)** whether it needs refactoring to reach good quality — and **if it does, refactor before closing**.

This is distinct from **D-088** (DDD/SOLID assessment at LOCK creation — same spirit, different moment) and reuses **D-085**'s `valida-pasta` rather than reimplementing scoring.

Then close, confirming the validation ran:

```text
finish <D-NNN> --docs-skip "..." --quality-checked --quality-skill clean-code-review --quality-finding "extraiu funcao X; cobriu caso Y"
# when there is genuinely nothing to assess (e.g. trivial constant/rename):
finish <D-NNN> --docs-skip "..." --quality-skip "alteracao trivial, sem impacto de qualidade"
```

The gate is a no-op when only `.guia/` bookkeeping changed, or when `finish.qualityGateByDefault` is `false` in `.guia/process.json`.

## 3) Close

Run this **only** because the developer asked for it (no env var or flag — see the rule above):

```text
finish <D-NNN> --docs-touched docs/reference/cli.md --quality-checked
# or, when nothing needed touching:
finish <D-NNN> --docs-skip "internal flow, no user-facing change" --quality-skip "no product code changed"
```

`finish` commits by default. Use `--no-commit` for dry close. Lock with `--lock --lock-id feature-slug --lock-description "..."` only when the developer asks for it.

{{include_per_target: _partials/post_cli}}

{{include: _partials/lock_protocol.md}}

Task is closed.
