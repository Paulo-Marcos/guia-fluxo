# Como editar um arquivo travado

Voce decidiu autorizar uma alteracao pontual em algo travado em [`features/registry.yaml`](../reference/registry-yaml.md).

## Checagem antes de editar

Antes de mexer no arquivo, o agente (ou voce) deve explicar:

- qual `id` de lock bloqueia o arquivo;
- qual funcionalidade esta protegida pela descricao do lock;
- por que a mudanca precisa tocar esse arquivo;
- impacto esperado na funcionalidade protegida;
- risco de regressao;
- alternativa sem mexer no arquivo travado, se existir.

So depois disso peca autorizacao explicita.

## Faca a alteracao e marque o commit

1. Edite o arquivo.
2. No commit, inclua a marca `[unlock:<id>]`:

   ```
   fix: corrige timestamp negativo no parser de VTT

   [unlock:ingestao-livestream] motivo: bug em legenda inicial < 0
   ```

3. O hook valida e aceita. O CI tambem valida no PR.
4. O desbloqueio fica no `git log` - auditavel para sempre.

## Destravar varias features no mesmo commit

Repita a marca:

```
fix: ajusta integracao entre ingestao e export

[unlock:ingestao-livestream] motivo: novo campo no contrato
[unlock:export-losslesscut] motivo: consumir o novo campo
```

## Atencao: unlock e por commit, nao por sessao

Se voce faz 3 commits seguidos mexendo na mesma feature, **cada um** precisa da marca. Isso e proposital - forca justificar cada toque.

## Casos especiais

- [Renomear ou mover um arquivo travado](renomear-arquivo-travado.md).
- Refactor cross-feature ou adicionar arquivo novo a uma feature travada: ver [explanation/convencoes-de-lock.md](../explanation/convencoes-de-lock.md#casos-especiais).

## Esqueci a marca e o commit foi bloqueado

```powershell
git commit --amend
# editor abre, adicione [unlock:<id>] motivo: ..., salve, feche
```

Se ja foi pushed em PR, faca novo commit com a marca (ou amend + force-push se for branch privado).
