# Como promover item do backlog

`/promote B-NNN` **nao** deve criar tarefa automaticamente sem raciocinio antes. O fluxo e deliberado: voce confirma escopo, plano e riscos.

## Fluxo obrigatorio

1. Ler o item em `.guia/backlog.json`.
2. Classificar como `feature` ou `issue`.
3. Avaliar se titulo/contexto sao suficientes.
4. Se faltar informacao, perguntar antes de criar demanda.
5. Propor plano curto de execucao.
6. Confrontar riscos: locks provaveis, funcionalidades impactadas e alternativas.
7. Perguntar se deve usar worktree.
8. Com OK do usuario, rodar o comando.

## Exemplo sem worktree

```powershell
.\core\bin\guia.ps1 promote B-019 --kind issue `
    --assessment "Regressao de agendamento" `
    --plan "Inspecionar servico de publicacao em massa"
```

## Exemplo com worktree

```powershell
.\core\bin\guia.ps1 promote B-019 --kind issue --worktree `
    --assessment "Regressao de agendamento" `
    --plan "Criar teste de intervalo antes do fix"
```

Quando uma task promovida com `--worktree` for finalizada, `finish` tenta remover a worktree registrada. O caminho padrao e `.claude/worktrees/<task-slug>` porque essa pasta ja e ignorada por padrao.

## Por que esse atrito proposital?

Ver [explanation/visao-geral.md](../explanation/visao-geral.md).

## Sintaxe completa

Ver [reference/cli.md](../reference/cli.md#promote).
