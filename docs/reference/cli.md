# Reference: CLI `core/src/guia.py` / `core/bin/guia.ps1`

Wrapper PowerShell `core/bin/guia.ps1` localiza o Python adequado e invoca `core/src/guia.py`. Tudo aqui vale para ambos.

## Subcomandos

### `init`

```powershell
.\core\bin\guia.ps1 init [--project-name "nome-do-projeto"] [--no-locks] [--force]
```

Inicializa o Guia Fluxo no projeto atual. Sempre semeia `.guia/` (JSONs vazios, `process.json` com o nome do projeto, `demand-title.txt` zerado). Por padrao tambem deploya, a partir do `templates/` do plugin (`${CLAUDE_PLUGIN_ROOT}/templates/`), a config de lock por-projeto e o hook:

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

Cria `D-NNN` com `kind=feature` (emoji ✨), atualiza `.guia/tasks.json`, `.guia/current-task.json` e `.guia/DEMANDAS.md`. Imprime `NOME DA DEMANDA: D-NNN ✨ - #DEV - ...`.

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

### `epic` (D-049)

```powershell
.\core\bin\guia.ps1 epic "Titulo do epico" --context "Por que isso virou epic"
.\core\bin\guia.ps1 feature "Sub-tarefa" --under E-001    # cria D-NNN filho de E-001
.\core\bin\guia.ps1 status E-001                          # arvore agregada
.\core\bin\guia.ps1 finish E-001                          # SO fecha quando todos os filhos forem terminais
```

Cria um Epic `E-NNN` (emoji 🎯) — orquestrador de stories. Numeracao independente de `D-NNN`. `--under E-NNN` em feature/bug/chore cria a story como filho. `status E-NNN` imprime arvore agregada (`Progresso: closed/total`). `finish E-NNN` e **recusado** enquanto qualquer filho estiver em status nao-terminal (Validada / Finalizada / Resolvida / Cancelada contam como terminais — mesmo set do D-067). **Hierarquia de 2 niveis** (sem epics aninhados); `parentId` e imutavel apos criacao. `cancel E-NNN` **nao** cascateia: filhos seguem como estao.

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

Mostra a tarefa atual e o titulo da demanda corrente (`NOME DA DEMANDA: ...`).

`--all` (B-014) imprime o quadro de todas as tasks `Em desenvolvimento`, marcando a `current`. Se houver mais de uma ativa ao mesmo tempo, avisa sobre a ambiguidade do `current-task.json` global (B-018) — comandos sem id explicito podem pegar a task errada.

### `ready`

```powershell
.\core\bin\guia.ps1 ready D-NNN `
    --file <caminho> [--file <outro>] `
    --summary "Resumo do que foi feito" `
    --validation "Comando ou check feito"
```

Move a task para `Aguardando validacao`. Gera relatorio em `.guia/reports/`. Imprime `NOME DA DEMANDA: D-NNN - #VALIDACAO - ...`.

### `finish`

```powershell
.\core\bin\guia.ps1 finish D-NNN `
    [--lock --lock-id <slug>] `
    [--docs-touched <path> ...] `
    [--docs-skip "<motivo>"] `
    [--quality-checked] [--quality-skill <nome> ...] [--quality-finding "<acao>" ...] `
    [--quality-skip "<motivo>"]
```

Marca como `Validada`, sugere `#FINALIZADO` e commita por padrao. Com `--lock`, registra os arquivos da task em `.guia/locks/registry.yaml` sob o slug informado.

**`finish` e acao do usuario (regra de comportamento, D-098).** Fechar e commitar e sempre decisao do desenvolvedor: o agente so roda `finish` quando o usuario solicita `/guia:finish` ou autoriza explicitamente, e **nunca** dispara por conta propria - o fluxo padrao da IA termina no `ready`. Isso e uma **regra de comportamento** (documentada na skill, no AGENTS.md e no CLAUDE.md), nao um parametro: `finish` nao exige env nem flag. (A D-098 removeu o gate por env `GUIA_HUMAN_FINISH` que a D-080 havia introduzido - mandar variavel era ruim e o motor nao consegue distinguir um agente de um humano sem um sinal artificial, entao o controle vive na instrucao do agente, nao no CLI.)

**Hook de docs (F-010).** Antes do fechamento, `finish` consulta `.guia/docs-map.yaml` (se existir) e computa candidatos de doc a atualizar. Quando ha candidatos, voce precisa registrar um dos flags abaixo, senao o comando aborta:

- `--docs-touched <path>` (repetivel): docs que voce atualizou nesta task.
- `--docs-skip "<motivo>"`: avaliou os candidatos e nada precisou mudar - escreva o motivo curto.
- `--docs-checked`: confirmacao explicita de que revisou (use em ultimo caso, ou junto com `--docs-touched`/`--docs-skip`).

O resultado fica em `task.docsReview` no `.guia/tasks.json`. Quando `.guia/docs-map.yaml` nao existe, o hook vira no-op com aviso no stderr. Detalhes em [`docs-map.md`](docs-map.md) e [`docs/how-to/manter-docs-atualizados.md`](../how-to/manter-docs-atualizados.md).

**Gate de qualidade (D-095).** Antes de fechar, `finish` forca uma validacao consultiva de qualidade do que foi feito (alem dos `validationCommands`). Quando arquivos de *produto* mudaram (qualquer coisa fora de `.guia/`), o comando recusa o fechamento ate o agente confirmar que rodou as skills de qualidade sobre `modifiedFiles`. Skills sao acionadas pelo **agente**, nao pelo Python: o core sinaliza+exige (imprime os arquivos, as dimensoes (a)–(e) e as skills candidatas — `clean-code-review`, `clean-architecture-guardian`, `tdd-dotnet`, `valida-pasta`/D-085) e a skill `guia:finish` instrui o agente a rodar e refatorar se preciso. Flags:

- `--quality-checked`: confirma que a validacao consultiva rodou sobre o que mudou.
- `--quality-skill <nome>` (repetivel): skill de qualidade acionada (ex.: `clean-code-review`).
- `--quality-finding "<acao>"` (repetivel): achado/refatoracao aplicada.
- `--quality-skip "<motivo>"`: nada a avaliar (ex.: alteracao trivial) — pula o gate com justificativa.

O resultado (skills, achados, dimensoes, ou skip) fica em `task.qualityReview` no `.guia/tasks.json`. O gate e no-op quando so `.guia/**` mudou ou quando `finish.qualityGateByDefault` e `false` no `.guia/process.json` (default `true`). Distinto de **D-088** (avalia DDD/SOLID ao criar LOCK) e reusa **D-085** (`valida-pasta`).

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

Bloqueia se a task ja esta em estado terminal (`Validada`, `Finalizada`, `Cancelada`). Imprime `NOME DA DEMANDA: D-NNN - #CANCELADA - ...`.

### `block`

```powershell
.\core\bin\guia.ps1 block D-NNN --reason "Por que esta pausando"
```

Pausa a task: status -> `Bloqueada`, preserva WIP, registra `task.blocks[] = [{reason, at}, ...]`. `--reason` e **obrigatorio**. Para retomar, use `unblock`.

Bloqueia se a task ja esta em estado terminal ou ja em `Bloqueada`. Imprime `NOME DA DEMANDA: D-NNN - #BLOQUEADA - ...`.

### `unblock`

```powershell
.\core\bin\guia.ps1 unblock D-NNN [--note "O que destravou"]
```

Retoma uma task pausada: status `Bloqueada` -> `Em desenvolvimento`. Fecha `task.blocks[-1].unblockedAt`. `--note` e opcional.

Falha se a task nao estava em `Bloqueada`. Imprime `NOME DA DEMANDA: D-NNN - #DEV - ...`.

### `validate` (deprecado)

Ainda existe como subcomando do CLI por compatibilidade. Nao ha mais skill para `/validate`. O fluxo recomendado e `/ready` -> humano testa -> `/finish`.

### `depends` (D-067)

Gerencia dependencias entre demandas. Uma task pode declarar que **depende** de outras; `start`/`promote` ficam **recusados** ate cada dependencia chegar a um status terminal (`Validada`, `Finalizada`, `Resolvida` ou `Cancelada`).

```powershell
# Declarar na criacao (repetivel):
.\core\bin\guia.ps1 feature "Titulo" --depends-on D-001 --depends-on D-002

# Pos-criacao:
.\core\bin\guia.ps1 depends add    [D-NNN] --on D-XYZ [--on D-ABC]
.\core\bin\guia.ps1 depends remove [D-NNN] --on D-XYZ
.\core\bin\guia.ps1 depends list   [D-NNN] [--json]
```

`add` recusa auto-dependencia, id inexistente em `tasks.json`, e qualquer dep que crie **ciclo** no grafo. `remove` e idempotente. `list` mostra cada dependencia com status atual e marca quais ainda bloqueiam.

### `stats` (D-052)

```powershell
.\core\bin\guia.ps1 stats [D-NNN] [--json]
```

Mostra o timing/throughput de uma task a partir dos timestamps ricos (ISO-8601 com timezone) capturados nas transicoes: `startedAt` (entrada em *Em desenvolvimento* via create/`start`/`promote`), `readyAt` (ultimo `ready`), `finishedAt` (terminal: Validada/Finalizada/Cancelada) e os intervalos de `blocks[]` (`blockedAt`/`unblockedAt`). Sem id, usa a task corrente.

Campos computados (segundos): `elapsedTotalSeconds` (= `finishedAt − startedAt`, wall-clock incl. pausas), `elapsedBlockedSeconds` (= Σ dos bloqueios fechados), `activeTimeSeconds` (= total − bloqueado); mais os contadores `blockCount`/`unblockCount`/`readyCount`. `--json` emite o objeto cru para consumo por agente. **Backfill:** tasks criadas antes do D-052 nao tem os campos e aparecem como `null` (nada e inventado).

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
