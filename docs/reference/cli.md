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
.\scripts\ai.ps1 finish F-NNN `
    [--lock --lock-id <slug>] `
    [--docs-touched <path> ...] `
    [--docs-skip "<motivo>"]
```

Marca como `Validada`, sugere `#FINALIZADO` e commita por padrao. Com `--lock`, registra os arquivos da task em `features/registry.yaml` sob o slug informado.

**Hook de docs (F-010).** Antes do fechamento, `finish` consulta `.ai/docs-map.yaml` (se existir) e computa candidatos de doc a atualizar. Quando ha candidatos, voce precisa registrar um dos flags abaixo, senao o comando aborta:

- `--docs-touched <path>` (repetivel): docs que voce atualizou nesta task.
- `--docs-skip "<motivo>"`: avaliou os candidatos e nada precisou mudar - escreva o motivo curto.
- `--docs-checked`: confirmacao explicita de que revisou (use em ultimo caso, ou junto com `--docs-touched`/`--docs-skip`).

O resultado fica em `task.docsReview` no `.ai/tasks.json`. Quando `.ai/docs-map.yaml` nao existe, o hook vira no-op com aviso no stderr. Detalhes em [`docs-map.md`](docs-map.md) e [`docs/how-to/manter-docs-atualizados.md`](../how-to/manter-docs-atualizados.md).

### `docs-check`

```powershell
.\scripts\ai.ps1 docs-check [F-NNN] [--json]
```

Lista docs candidatos a atualizacao para a task indicada (ou a task corrente, se omitida). Le `.ai/docs-map.yaml` e aplica triggers contra `task.modifiedFiles` + `git diff --name-only HEAD`. Nao muda estado, e seguro de rodar a qualquer momento.

- Sem `--json`: imprime em texto com `purpose`, `motivo` e `hint` por candidato.
- Com `--json`: retorna `{hasMap, taskId, candidates: [...]}` para consumo por agente.

Quando o mapa nao existe, retorna `{"hasMap": false, "candidates": []}` (JSON) ou aviso curto (texto).

### `validate` (deprecado)

Ainda existe como subcomando do CLI por compatibilidade. Nao ha mais skill para `/validate`. O fluxo recomendado e `/ready` -> humano testa -> `/finish`.

### `render`

```powershell
.\scripts\ai.ps1 render [--check] [--verb <nome>]
```

Wrapper de `scripts/render-skills.py`. Regenera as skills a partir de `skills/manifest.yaml` em quatro destinos:

- `skills/generated/.claude/skills/<verbo>/SKILL.md` - stage de distribuicao para Claude Code.
- `skills/generated/.agents/skills/<verbo>/SKILL.md` - stage de distribuicao para Codex + Antigravity.
- `.claude/skills/<verbo>/SKILL.md` - ativo runtime do dogfood deste repo (Claude Code descobre as skills aqui).
- `.agents/skills/<verbo>/SKILL.md` - ativo runtime do dogfood deste repo (Codex/Antigravity).

Cada verbo do manifest emite quatro arquivos. `--check` sai com codigo != 0 se qualquer um estiver fora de sincronia. `--verb <nome>` limita o render a um verbo especifico.

Os destinos em `skills/generated/` sao copiados pra raiz dos projetos consumidores na instalacao. Os destinos na raiz so existem aqui (no repo-mae) - sao o que faz `/feature`, `/issue` etc. funcionarem enquanto voce desenvolve o pack.

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
