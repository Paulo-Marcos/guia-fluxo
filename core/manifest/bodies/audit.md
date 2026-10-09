# Audit

Audit the PR head adversarially: read everything before executing anything from the PR.

{{include_per_target: _partials/run_cmd}}

```text
audit [D-NNN]                                     # what to audit (skill or checklist)
audit [D-NNN] --report report.md --approve --finding BLOQUEANTE=0 --finding CORRIGIR=0 --skill-ran pr-audit
```

- The marker must point at the head GitHub sees: push (or `ship`) first.
- Without `--finding`, the `pilot` level never closes the demand on its own.

{{include_per_target: _partials/post_cli}}
