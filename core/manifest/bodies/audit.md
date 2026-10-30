# Audit

Audit the PR head adversarially: read everything before executing anything from the PR.

{{include_per_target: _partials/run_cmd}}

```text
audit [D-NNN]                                     # what to audit (skill or checklist)
audit [D-NNN] --report report.md --approve --finding BLOQUEANTE=0 --finding CORRIGIR=0 --skill-ran pr-audit
```

- The marker must point at the head GitHub sees: push (or `ship`) first.
- Without `--finding`, the `pilot` level never closes the demand on its own.
- After a rejected audit, fix the findings on the branch and `ship`: the next `audit` prints the `git range-diff` since the rejected head and the previous findings - audit only that delta, confirm each finding closed and that the fix did not touch what was already ok. The engine switches back to a full audit (and says why) when the delta is large or touches workflows, hooks, locks, agent config, dependencies or security paths.
- Write each finding as a `- [SEVERITY] path:line - ...` line in the report: the engine keeps them for the next round.
- Next step after an approved audit: `queue add` (levels `queue`/`pilot`) - never merge the PR yourself.

{{include_per_target: _partials/post_cli}}

{{include: _partials/conductor.md}}
