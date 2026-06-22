<!--
Template aplicado a todo PR. Apague o que nao se aplica.
Veja docs/how-to/ antes de abrir o PR.
-->

## Resumo

<!-- 1-2 frases. O que mudou e por que. -->

## Demanda relacionada

<!-- ID da demanda (D-###) e link, se houver. -->

- Demanda: F-### / I-###

## O que mudou

- [ ] Codigo
- [ ] Documentacao (`docs/` ou `README.md`)
- [ ] Skills (`core/manifest/manifest.yaml` + `dist/skills/` + `dist/.agents/skills/`)
- [ ] Templates de bootstrap (`core/templates/`)
- [ ] Lock (`.guia/locks/registry.yaml`)
- [ ] Outro: <!-- ... -->

## Como testei

<!-- Comandos que voce rodou e o que esperava ver. Cole saidas relevantes. -->

```
python core/src/guia.py doctor
python core/build/render-skills.py --check
```

## Locks tocados

<!--
Se o PR modifica arquivo travado em .guia/locks/registry.yaml, cada commit
relevante precisa ter [unlock:<feature-id>] motivo: ... na mensagem.
O workflow .github/workflows/lock-check.yml re-checa no PR e barra merge.
Liste aqui quais features foram desbloqueadas e por que.
-->

- [ ] PR nao toca em arquivo travado.
- [ ] PR toca em arquivo travado e os commits trazem `[unlock:<id>]`.

## Checklist final

- [ ] `python core/src/guia.py doctor` passa.
- [ ] `python core/build/render-skills.py --check` passa (se mexeu em skills).
- [ ] Demanda no `.guia/DEMANDAS.md` atualizada via `ready`/`finish`.
- [ ] Documentacao atualizada (se mudou comportamento).
