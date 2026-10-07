# Finish

Close an already-validated task. Run **only after** the developer confirms validation in real use — `finish` is the closing gate, not a shortcut.

> **`finish` is the USER's action (behavioral rule, D-098).** Closing is the developer's call. **If you are an AI agent, run `finish` ONLY when the developer requests `/guia:finish` or explicitly authorizes it — NEVER on your own initiative.** Your default job ends at `ready`: hand off and wait for the developer to ask for the close. This is a behavioral rule, not a CLI parameter — there is no env var or flag to set (D-098 removed the `GUIA_HUMAN_FINISH` env gate the earlier D-080 had tried; sending a variable was bad, and the engine cannot tell an agent apart from a human anyway).

> **Always pass the explicit demand id of THIS chat (behavioral rule, D-103).** `finish` is terminal and irreversible. **Never run bare `finish`** — the engine no longer falls back to `current-task.json` (a single per-working-copy pointer that another session/chat can silently drift to a demand this chat never touched; that footgun once closed the wrong task). Deduce the id from the conversation — the demand this chat created and worked on (the `NOME DA DEMANDA: D-NNN ...` line the CLI printed), **not** from the current-task pointer — and pass it: `finish D-NNN`. If ever unsure which demand is active here, run `status --all` and confirm with the developer before closing. Bare `finish` is rejected and lists the `Aguardando validacao` candidates to help you pick.

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
finish <D-NNN> --file <path> [--file <path> ...] --docs-touched docs/reference/cli.md --quality-checked
# or, when nothing needed touching:
finish <D-NNN> --file <path> --docs-skip "internal flow, no user-facing change" --quality-skip "no product code changed"
```

> **Declare the demand's files with `--file` (behavioral rule, D-105).** When committing, `finish` no longer infers the file set from the whole tree. `git diff HEAD` sees the work of every demand running in parallel in the same working copy, and the old `git add -A` swallowed it into the closing commit (the reason `--no-commit` was a workaround). Now the commit is **scoped to the pathspecs you declare** (or that a prior `ready` accumulated) — pass one `--file` per file **this** demand touched. A committing `finish` with no product file declared is **refused** with a message asking for `--file`. You no longer need `--no-commit` to avoid swallowing concurrent work; it survives only as a genuine dry-close.

`finish` commits by default (now isolated to your `--file` set). Use `--no-commit` for a real dry close. **In `delivery.mode: "pr"` it never commits** (D-111): the code reaches `main` through the PR squash, so `finish` only closes the state, and `--commit` is refused. Lock with `--lock --lock-id feature-slug --lock-description "..."` only when the developer asks for it.

{{include_per_target: _partials/post_cli}}

{{include: _partials/lock_protocol.md}}

Task is closed.
