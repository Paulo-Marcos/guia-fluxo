# Bug

Create a bug task before editing code. Use for a regression, a defect, or any incorrect behavior that needs investigation and fix.

{{include: _partials/title_context_rules.md}}

{{include_per_target: _partials/run_cmd}}

```text
bug "<title>" --context "<observed symptom + impact>"
```

Useful flags:
- `--context "<symptom + impact>"` — observed behavior vs expected, who is affected.
- `--status backlog|planned|in-development` (default `in-development`) — `backlog` if not triaged, `planned` if planned but not now.
- `--origin "<source>"` — alternate origin.

{{include_per_target: _partials/post_cli}}

{{include: _partials/lock_protocol.md}}

## Regression test before the fix

Every bug is fixed in this order — the test is the proof that the bug existed and is gone:

1. **Write the test first**, reproducing the reported behavior with synthetic data. Run it and **see it fail** for the reason in the report. A test that passes before the fix proves nothing.
2. **Fix**, then see the same test pass. Keep the test: it guards against the bug coming back.
3. **Only the fix.** No drive-by refactor, no speculative abstraction, no weakened or deleted test, no TODO left behind — those are separate tasks.
4. If a test is genuinely impossible (pure visual glitch, timing on real hardware), say so in `--validation` and describe the manual check that replaces it.

Record the before/after in `ready --validation` (e.g. "test X failed on HEAD before the fix, passes after").

Then continue with the investigation and fix.
