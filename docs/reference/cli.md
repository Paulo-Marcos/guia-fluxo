# Reference: CLI `core/src/guia.py` / `core/bin/guia.ps1`

Wrapper PowerShell `core/bin/guia.ps1` localiza o Python adequado e invoca `core/src/guia.py`. Tudo aqui vale para ambos.

## Subcomandos

### `init`

```powershell
.\core\bin\guia.ps1 init [--project-name "nome-do-projeto"] [--no-locks] [--force]
```

Inicializa o Guia Fluxo no projeto atual. Sempre semeia `.guia/` (JSONs vazios, `process.json` com o nome do projeto, `chat-title.txt` zerado). Por padrao tambem deploya, a partir do `templates/` do plugin (`${CLAUDE_PLUGIN_ROOT}/templates/`), a config de lock por-projeto e o hook:

- `.guia/locks/registry.yaml`, `.guia/locks/lock-ignore.txt`
- `.githooks/commit-msg` + `git config core.hooksPath .githooks` (so se ainda nao definido)

Idempotente e **nunca clobbera** arquivos existentes (imprime `+` para escritos e `=` para preservados). `--no-locks` faz so o seed de `.guia/`; `--force` sobrescreve. No Claude Code o auto-init ja cria `.guia/` no primeiro comando — rode `init` para optar pelos locks.

### `upgrade`

```powershell
.\core\bin\guia.ps1 upgrade [--dry-run]
```

Migra um projeto **existente** do layout antigo (pre-D-055/D-056) para o atual: `FEATURES.md` (raiz) → `.guia/DEMANDAS.md`, `features/registry.yaml` → `.guia/locks/registry.yaml`, `features/lock-ignore.txt` → `.guia/locks/lock-ignore.txt`, e remove `features/` se ficou vazio. Usa `git mv` quando o arquivo esta rastreado (preserva historico de rename). Idempotente: NOOP quando nada ha pra mover. `--dry-run` lista o plano sem mutar. Recusa (exit 1) se algum destino ja existe — resolva a mao e re-rode. Distinto de `init` (setup virgem), `/plugin update` (atualiza o plugin) e `backlog migrate` (`B-NNN` legacy).

### `doctor`

```powershell
.\core\bin\guia.ps1 doctor
```

Sanity check: confirma layout, dependencias e que os arquivos esperados existem.

### `feature`

```powershell
.\core\bin\guia.ps1 feature "Titulo curto" --context "Motivo e escopo" `
    [--status backlog|planned|in-development]
```

Cria `D-NNN` com `kind=feature` (emoji ✨), atualiza `.guia/tasks.json`, `.guia/current-task.json` e `.guia/DEMANDAS.md`. Imprime `NOME DO CHAT: D-NNN ✨ - #DEV - ...`.

`--status` (ADR-0011 Fase 3) controla o estado inicial: `backlog` parqueia sem catalogar; `planned` triada mas nao iniciada; `in-development` (default) ja em curso.

### `bug`

```powershell
.\core\bin\guia.ps1 bug "Sintoma curto" --context "Impacto e reproducao" `
    [--status backlog|planned|in-development]
```

Cria `D-NNN` com `kind=bug` (emoji 🐛). Substitui o antigo `issue`, removido na Fase 4 do ADR-0011 — o nome `issue` colidia com o sentido guarda-chuva da industria.

### `chore`

```powershell
.\core\bin\guia.ps1 chore "Titulo curto" --context "O que e por que" `
    [--status backlog|planned|in-development]
```

Cria `D-NNN` com `kind=chore` (emoji 🧹). Use para manutencao que merece rastro mas nao e feature nem bug: refactor pequeno, atualizar dependencia, ajustar build/lint, organizar pasta.

### `backlog`

```powershell
.\core\bin\guia.ps1 backlog add "Ideia futura" --context "Quando pode ser util"
.\core\bin\guia.ps1 backlog list
.\core\bin\guia.ps1 backlog migrate [--dry-run] [--force]
.\core\bin\guia.ps1 backlog resolve D-NNN [--reason "Por que saiu do backlog"]
```

`add` cria `D-NNN` com `kind=feature` (default) e `status=Backlog` em `.guia/tasks.json` (ADR-0011 Fase 2: backlog.json deixou de ser source-of-truth para novas entradas). Nao entra em `.guia/DEMANDAS.md` ate ser promovido.

`list` une fontes: `tasks.json` com `status=Backlog` primeiro, depois itens legacy de `backlog.json` (`B-NNN`). Itens resolvidos (`resolve`) nao aparecem.

`migrate` (Fase 2): copia itens `B-NNN` legacy de `backlog.json` para `tasks.json` preservando o ID. `--dry-run` (default) so lista o plano; `--force` aplica e esvazia `backlog.json`. Idempotente: pula itens cujo ID ja existe em `tasks.json`.

`resolve` retira do backlog ativo um item ja entregue por outra demanda (ou obsoleto), sem promover: marca `status=Resolvida` + `resolvedAt` (+ `resolution` se `--reason`) e o item some de `list`, preservado no arquivo para historico. Funciona nas duas fontes (`D-NNN` em `tasks.json` e `B-NNN` legacy). Idempotente. Diferente de `cancel` (que e para task em andamento) e de `promote` (que inicia o trabalho).

### `promote`

```powershell
.\core\bin\guia.ps1 promote <id> --kind {feature|bug|chore} `
    --assessment "Avaliacao curta" `
    --plan "Plano de execucao" `
    [--worktree]
```

Promove um item de backlog para `Em desenvolvimento`. Aceita `<id>` em dois formatos: `D-NNN` (task em `tasks.json` com `status=Backlog`) ou `B-NNN` legacy (em `backlog.json`).

- **D-NNN**: promote in-place. ID preservado; `status` muda para `Em desenvolvimento`; `kind` atualizado via `--kind`.
- **B-NNN legacy**: cria task nova `D-NNN` com `backlogId=B-NNN` apontando para o legacy; o B-NNN e removido de `backlog.json`.

Quando `--worktree` e passado, `finish` removera a worktree associada.

**Importante:** o agente nao deve invocar `promote` sem antes seguir o fluxo de avaliacao. Ver [how-to/promover-backlog.md](../how-to/promover-backlog.md).

### `plan`

```powershell
.\core\bin\guia.ps1 plan <id> [--note "Por que esta planejando"]
```

Move task para `Planejada` (triada mas nao iniciada — ADR-0011 Fase 3 / B-017). Aceita transicao de `Backlog` ou `Em desenvolvimento`. Falha em estados terminais ou se ja `Planejada`.

### `start`

```powershell
.\core\bin\guia.ps1 start <id> [--note "Comecando agora porque..."]
```

Move task para `Em desenvolvimento`. Aceita transicao de `Backlog` (atalho que pula `Planejada`) ou `Planejada`. Pressupoe que a triagem (kind) ja foi feita — para triar avaliando feature/bug/chore, use `promote`.

### `status`

```powershell
.\core\bin\guia.ps1 status
.\core\bin\guia.ps1 status --all
```

Mostra a tarefa atual e o titulo sugerido para o chat.

`--all` (B-014) imprime o quadro de todas as tasks `Em desenvolvimento`, marcando a `current`. Se houver mais de uma ativa ao mesmo tempo, avisa sobre a ambiguidade do `current-task.json` global (B-018) — comandos sem id explicito podem pegar a task errada.

### `ready`

```powershell
.\core\bin\guia.ps1 ready D-NNN `
    --file <caminho> [--file <outro>] `
    --summary "Resumo do que foi feito" `
    --validation "Comando ou check feito"
```

Move a task para `Aguardando validacao`. Gera relatorio em `.guia/reports/`. Imprime `NOME DO CHAT: D-NNN - #VALIDACAO - ...`.

### `finish`

```powershell
.\core\bin\guia.ps1 finish D-NNN `
    [--lock --lock-id <slug>] `
    [--docs-touched <path> ...] `
    [--docs-skip "<motivo>"]
```

Marca como `Validada`, sugere `#FINALIZADO` e commita por padrao. Com `--lock`, registra os arquivos da task em `.guia/locks/registry.yaml` sob o slug informado.

**Hook de docs (F-010).** Antes do fechamento, `finish` consulta `.guia/docs-map.yaml` (se existir) e computa candidatos de doc a atualizar. Quando ha candidatos, voce precisa registrar um dos flags abaixo, senao o comando aborta:

- `--docs-touched <path>` (repetivel): docs que voce atualizou nesta task.
- `--docs-skip "<motivo>"`: avaliou os candidatos e nada precisou mudar - escreva o motivo curto.
- `--docs-checked`: confirmacao explicita de que revisou (use em ultimo caso, ou junto com `--docs-touched`/`--docs-skip`).

O resultado fica em `task.docsReview` no `.guia/tasks.json`. Quando `.guia/docs-map.yaml` nao existe, o hook vira no-op com aviso no stderr. Detalhes em [`docs-map.md`](docs-map.md) e [`docs/how-to/manter-docs-atualizados.md`](../how-to/manter-docs-atualizados.md).

### `docs-check`

```powershell
.\core\bin\guia.ps1 docs-check [D-NNN] [--json]
```

Lista docs candidatos a atualizacao para a task indicada (ou a task corrente, se omitida). Le `.guia/docs-map.yaml` e aplica triggers contra `task.modifiedFiles` + `git diff --name-only HEAD`. Nao muda estado, e seguro de rodar a qualquer momento.

- Sem `--json`: imprime em texto com `purpose`, `motivo` e `hint` por candidato.
- Com `--json`: retorna `{hasMap, taskId, candidates: [...]}` para consumo por agente.

Quando o mapa nao existe, retorna `{"hasMap": false, "candidates": []}` (JSON) ou aviso curto (texto).

### `cancel`

```powershell
.\core\bin\guia.ps1 cancel D-NNN --reason "Motivo curto" `
    [--keep-worktree] `
    [--set-current]
```

Encerra a task como `Cancelada` (estado terminal). `--reason` e **obrigatorio** (fica em `task.cancellations[]` e no historico em `.guia/DEMANDAS.md`).

- `--keep-worktree`: nao remove a worktree associada. Default: remove se a task tinha worktree.
- `--set-current`: mantem a task como current apos cancelar. Default: limpa `.guia/current-task.json` se a task cancelada era a current.

Bloqueia se a task ja esta em estado terminal (`Validada`, `Finalizada`, `Cancelada`). Imprime `NOME DO CHAT: D-NNN - #CANCELADA - ...`.

### `block`

```powershell
.\core\bin\guia.ps1 block D-NNN --reason "Por que esta pausando"
```

Pausa a task: status -> `Bloqueada`, preserva WIP, registra `task.blocks[] = [{reason, at}, ...]`. `--reason` e **obrigatorio**. Para retomar, use `unblock`.

Bloqueia se a task ja esta em estado terminal ou ja em `Bloqueada`. Imprime `NOME DO CHAT: D-NNN - #BLOQUEADA - ...`.

### `unblock`

```powershell
.\core\bin\guia.ps1 unblock D-NNN [--note "O que destravou"]
```

Retoma uma task pausada: status `Bloqueada` -> `Em desenvolvimento`. Fecha `task.blocks[-1].unblockedAt`. `--note` e opcional.

Falha se a task nao estava em `Bloqueada`. Imprime `NOME DO CHAT: D-NNN - #DEV - ...`.

### `validate` (deprecado)

Ainda existe como subcomando do CLI por compatibilidade. Nao ha mais skill para `/validate`. O fluxo recomendado e `/ready` -> humano testa -> `/finish`.

### `render`

```powershell
.\core\bin\guia.ps1 render [--check] [--verb <nome>]
```

Wrapper de `core/build/render-skills.py`. Regenera as skills a partir de `core/manifest/manifest.yaml` em dois destinos:

- `plugins/guia/commands/<verbo>.md` - plugin command do Claude Code (`plugins/guia/.claude-plugin/plugin.json`, namespace `guia`). Surgem namespaced como `/guia:feature`, `/guia:bug`, `/guia:chore`, etc. (commands namespaceiam; skills surgiriam bare).
- `plugins/guia/.agents/skills/<verbo>/SKILL.md` - convencao AGENTS.md cross-tool para Codex + Antigravity.

Cada verbo do manifest emite dois arquivos. `--check` sai com codigo != 0 se qualquer um estiver fora de sincronia. `--verb <nome>` limita o render a um verbo especifico.

Os dois destinos sao distribuiveis: ao instalar o pack em outro projeto, copie `plugins/guia/commands/` (Claude) e/ou `plugins/guia/.agents/skills/` (Codex/Antigravity) junto com `plugins/guia/.claude-plugin/plugin.json`, `core/manifest/manifest.yaml`, `core/src/guia.py`, `core/bin/guia.ps1` e `.guia/`. Decisao arquitetural em [`docs/adr/0006-plugin-oficial-claude-code.md`](../adr/0006-plugin-oficial-claude-code.md).

## Aliases conversacionais

Os comandos acima sao expostos para agentes via skills/shims. No Claude Code (plugin oficial, namespace `guia`) os atalhos saem namespaced; em Codex/Antigravity (via `plugins/guia/.agents/skills/`) o nome curto continua valendo:

| Alias Claude | Alias Codex/Antigravity | Subcomando | Emoji |
| --- | --- | --- | --- |
| `/guia:feature` | `/feature` ou `$feature` | `feature` | ✨ |
| `/guia:bug` | `/bug` ou `$bug` | `bug` | 🐛 |
| `/guia:chore` | `/chore` ou `$chore` | `chore` | 🧹 |
| `/guia:backlog` | `/backlog` ou `$backlog` | `backlog` | — |
| `/guia:promote <id>` | `/promote` ou `$promote` | `promote` | — |
| `/guia:plan` | `/plan` ou `$plan` | `plan` | — |
| `/guia:start` | `/start` ou `$start` | `start` | — |
| `/guia:ready` | `/ready` ou `$ready` | `ready` | — |
| `/guia:finish` | `/finish` ou `$finish` | `finish` | — |
| `/guia:cancel` | `/cancel` ou `$cancel` | `cancel` | — |
| `/guia:block` | `/block` ou `$block` | `block` | — |
| `/guia:unblock` | `/unblock` ou `$unblock` | `unblock` | — |
| `/guia:status` | `/status` ou `$status` | `status` | — |

> **Removido na Fase 4 do ADR-0011 (2026-06-07):** `/guia:issue` e `ai issue` nao existem mais — use `/guia:bug`. Tasks legacy com `kind=issue` (ex.: `I-006`) continuam navegaveis e renderizam como "Bug (legacy)" 🐛 em `.guia/DEMANDAS.md`.
