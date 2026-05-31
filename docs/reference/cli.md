# Reference: CLI `ai.py` / `ai.ps1`

Wrapper PowerShell `scripts/ai.ps1` localiza o Python adequado e invoca `scripts/ai.py`. Tudo aqui vale para ambos.

## Subcomandos

### `init`

```powershell
.\scripts\ai.ps1 init --project-name "nome-do-projeto"
```

Cria os JSONs vazios em `.ai/`, escreve `process.json` com o nome do projeto e zera `chat-title.txt`.

### `doctor`

```powershell
.\scripts\ai.ps1 doctor
```

Sanity check: confirma layout, dependencias e que os arquivos esperados existem.

### `feature`

```powershell
.\scripts\ai.ps1 feature "Titulo curto" --context "Motivo e escopo"
```

Cria `F-NNN`, atualiza `.ai/tasks.json`, `.ai/current-task.json` e `FEATURES.md`. Imprime `NOME DO CHAT: F-NNN - #DEV - ...`.

### `issue`

```powershell
.\scripts\ai.ps1 issue "Bug observado" --context "Sintoma e impacto"
```

Cria `I-NNN`. Demais comportamentos identicos ao `feature`.

### `backlog`

```powershell
.\scripts\ai.ps1 backlog add "Ideia futura" --context "Quando pode ser util"
.\scripts\ai.ps1 backlog list
```

`add` cria `B-NNN` em `.ai/backlog.json`. `list` enumera o backlog atual.

### `promote`

```powershell
.\scripts\ai.ps1 promote B-NNN --kind {feature|issue} `
    --assessment "Avaliacao curta" `
    --plan "Plano de execucao" `
    [--worktree]
```

Promove item do backlog para feature ou issue. Quando `--worktree` e passado, `finish` removera a worktree associada.

**Importante:** o agente nao deve invocar `promote` sem antes seguir o fluxo de avaliacao. Ver [how-to/promover-backlog.md](../how-to/promover-backlog.md).

### `status`

```powershell
.\scripts\ai.ps1 status
```

Mostra a tarefa atual e o titulo sugerido para o chat.

### `ready`

```powershell
.\scripts\ai.ps1 ready F-NNN `
    --file <caminho> [--file <outro>] `
    --summary "Resumo do que foi feito" `
    --validation "Comando ou check feito"
```

Move a task para `Aguardando validacao`. Gera relatorio em `.ai/reports/`. Imprime `NOME DO CHAT: F-NNN - #VALIDACAO - ...`.

### `finish`

```powershell
.\scripts\ai.ps1 finish F-NNN [--lock --lock-id <slug>]
```

Marca como `Validada`, sugere `#FINALIZADO` e commita por padrao. Com `--lock`, registra os arquivos da task em `features/registry.yaml` sob o slug informado.

### `validate` (deprecado)

Ainda existe como subcomando do CLI por compatibilidade. Nao ha mais skill para `/validate`. O fluxo recomendado e `/ready` -> humano testa -> `/finish`.

### `render`

```powershell
.\scripts\ai.ps1 render [--check] [--verb <nome>]
```

Wrapper de `scripts/render-skills.py`. Regenera `skills/generated/` a partir de `skills/manifest.yaml`.

- `--check`: nao escreve. Sai com codigo != 0 se houver drift entre manifest e geracao.
- `--verb <nome>`: limita o render a um verbo especifico.

## Aliases conversacionais

Os comandos acima sao expostos para agentes via skills/shims:

| Alias | Subcomando |
| --- | --- |
| `/feature` | `feature` |
| `/issue` | `issue` |
| `/backlog` | `backlog` |
| `/promote B-NNN` | `promote` |
| `/ready` | `ready` |
| `/finish` | `finish` |
| `/status` | `status` |
