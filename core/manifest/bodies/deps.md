# Deps

The Dependabot PRs, handled as one batch demand. Without `--now` this only shows them (read-only). With `--now` you **conduct the batch end to end**: the level of the batch decides how far you go alone, and you stop only when there is something to decide.

{{include_per_target: _partials/run_cmd}}

```text
deps [--json]          # show the bot PRs, the open batch, its level and the stage skill
deps --now --json      # create the batch demand (or return the open one) and conduct it
```

## Conducting the batch (`--now`)

1. **Read the batch.** `deps --now --json` gives `openLote` (the batch demand), `level`, `skills` (the `deps` stage skill, default `pr-bump`) and `security`. No `openLote`: there are no bumps - say so and end.
2. **Set it up.** `start <lote>` (when it is still `Planejada`), `worktree add <lote>`, and name and record the chat as the post-CLI steps say.
3. **Run the stage skill** listed in `skills`, inside the batch worktree, over the PRs of the batch. If it is not available in this session, **stop and tell the developer** - joining versions without it is guesswork, not mechanics. The skill brings each package to the newest compatible version, applies the supply-chain floor and runs the gate once.
4. **Only ask when there is a real decision.** A major version that breaks the code, a supply-chain doubt (new registry, look-alike name, git source), a ratchet baseline that must be re-measured: ask the developer, one decision at a time, with the evidence. Routine bumps are not decisions.
5. **Hand over.** `ready <lote>` with the Request -> Test lines, then let the engine conduct (below) - `ship`, audit, `queue add`. At the `pilot` level, a batch that only changes versions (manifests/lockfiles, workflow `uses:` lines, its own changelog fragment) enters the queue approved; anything beyond that stops at the owner with the reason. A security batch enters as `hotfix`. The queue integrates it and closes the incorporated bot PRs.

{{include: _partials/conductor.md}}

{{include_per_target: _partials/post_cli}}
