# Reference: CLI `core/src/ai.py` / `core/bin/ai.ps1`

Wrapper PowerShell `core/bin/ai.ps1` localiza o Python adequado e invoca `core/src/ai.py`. Tudo aqui vale para ambos.

## Subcomandos

### `init`

```powershell
.\core\bin\ai.ps1 init --project-name "nome-do-projeto"
```

Cria os JSONs vazios em `.ai/`, escreve `process.json` com o nome do projeto e zera `chat-title.txt`.

### `doctor`

```powershell
.\core\bin\ai.ps1 doctor
```

Sanity check: confirma layout, dependencias e que os arquivos esperados existem.

### `feature`

```powershell
.\core\bin\ai.ps1 feature "Titulo curto" --context "Motivo e escopo"
```

Cria `F-NNN`, atualiza `.ai/tasks.json`, `.ai/current-task.json` e `FEATURES.md`. Imprime `NOME DO CHAT: F-NNN - #DEV - ...`.

### `issue`

```powershell
.\core\bin\ai.ps1 issue "Bug observado" --context "Sintoma e impacto"
```

Cria `I-NNN`. Demais comportamentos identicos ao `feature`.

### `backlog`

```powershell
.\core\bin\ai.ps1 backlog add "Ideia futura" --context "Quando pode ser util"
.\core\bin\ai.ps1 backlog list
```

`add` cria `B-NNN` em `.ai/backlog.json`. `list` enumera o backlog atual.

### `promote`

```powershell
.\core\bin\ai.ps1 promote B-NNN --kind {feature|issue} `
    --assessment "Avaliacao curta" `
    --plan "Plano de execucao" `
    [--worktree]
```

Promove item do backlog para feature ou issue. Quando `--worktree` e passado, `finish` removera a worktree associada.

**Importante:** o agente nao deve invocar `promote` sem antes seguir o fluxo de avaliacao. Ver [how-to/promover-backlog.md](../how-to/promover-backlog.md).

### `status`

```powershell
.\core\bin\ai.ps1 status
```

Mostra a tarefa atual e o titulo sugerido para o chat.

### `ready`

```powershell
.\core\bin\ai.ps1 ready F-NNN `
    --file <caminho> [--file <outro>] `
    --summary "Resumo do que foi feito" `
    --validation "Comando ou check feito"
```

Move a task para `Aguardando validacao`. Gera relatorio em `.ai/reports/`. Imprime `NOME DO CHAT: F-NNN - #VALIDACAO - ...`.

### `finish`

```powershell
.\core\bin\ai.ps1 finish F-NNN `
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
.\core\bin\ai.ps1 docs-check [F-NNN] [--json]
```

Lista docs candidatos a atualizacao para a task indicada (ou a task corrente, se omitida). Le `.ai/docs-map.yaml` e aplica triggers contra `task.modifiedFiles` + `git diff --name-only HEAD`. Nao muda estado, e seguro de rodar a qualquer momento.

- Sem `--json`: imprime em texto com `purpose`, `motivo` e `hint` por candidato.
- Com `--json`: retorna `{hasMap, taskId, candidates: [...]}` para consumo por agente.

Quando o mapa nao existe, retorna `{"hasMap": false, "candidates": []}` (JSON) ou aviso curto (texto).

### `validate` (deprecado)

Ainda existe como subcomando do CLI por compatibilidade. Nao ha mais skill para `/validate`. O fluxo recomendado e `/ready` -> humano testa -> `/finish`.

### `render`

```powershell
.\core\bin\ai.ps1 render [--check] [--verb <nome>]
```

Wrapper de `core/build/render-skills.py`. Regenera as skills a partir de `core/manifest/manifest.yaml` em dois destinos:

- `dist/skills/<verbo>/SKILL.md` - output oficial do plugin Claude Code (`dist/.claude-plugin/plugin.json`, namespace `ai`). Atalhos saem como `/ai:feature`, `/ai:issue`, etc.
- `dist/.agents/skills/<verbo>/SKILL.md` - convencao AGENTS.md cross-tool para Codex + Antigravity.

Cada verbo do manifest emite dois arquivos. `--check` sai com codigo != 0 se qualquer um estiver fora de sincronia. `--verb <nome>` limita o render a um verbo especifico.

Os dois destinos sao distribuiveis: ao instalar o pack em outro projeto, copie `dist/skills/` (Claude) e/ou `dist/.agents/skills/` (Codex/Antigravity) junto com `dist/.claude-plugin/plugin.json`, `core/manifest/manifest.yaml`, `core/src/ai.py`, `core/bin/ai.ps1` e `.ai/`. Decisao arquitetural em [`docs/adr/0006-plugin-oficial-claude-code.md`](../adr/0006-plugin-oficial-claude-code.md).

## Aliases conversacionais

Os comandos acima sao expostos para agentes via skills/shims. No Claude Code (plugin oficial, namespace `ai`) os atalhos saem namespaced; em Codex/Antigravity (via `dist/.agents/skills/`) o nome curto continua valendo:

| Alias Claude | Alias Codex/Antigravity | Subcomando |
| --- | --- | --- |
| `/ai:feature` | `/feature` ou `$feature` | `feature` |
| `/ai:issue` | `/issue` ou `$issue` | `issue` |
| `/ai:backlog` | `/backlog` ou `$backlog` | `backlog` |
| `/ai:promote B-NNN` | `/promote` ou `$promote` | `promote` |
| `/ai:ready` | `/ready` ou `$ready` | `ready` |
| `/ai:finish` | `/finish` ou `$finish` | `finish` |
| `/ai:status` | `/status` ou `$status` | `status` |
