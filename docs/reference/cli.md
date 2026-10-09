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

Sanity check: confirma layout, dependencias e que os arquivos esperados existem. `.guia/process.json` (configuracao) e obrigatorio; `tasks.json`, `backlog.json` e `current-task.json` (estado) ausentes geram so aviso, porque o estado pode estar fora do git (checkout limpo do CI) ou o projeto ainda nao ter demandas (D-106). `--strict` promove avisos a erro.

**Fatos de entrega (`--delivery`, D-117).** `doctor --delivery [--json]` lista, cada um com a fonte: remoto GitHub, `gh` autenticado, protecao da base (checks exigidos, `strict`, `enforce_admins`, historico linear), metodos de merge e auto-merge, workflow de auditoria (`issue_comment` que grava status, e o contexto), agregador de CI (job com `if: always()` e `needs`), CHANGELOG (Keep a Changelog, `[Unreleased]`, pasta de fragmentos), release (`bin/release.*`, workflow de tag, `VERSION`) e hooks. So leitura, pelo `gh` (nada de token proprio); fato que nao pode ser lido vem vazio com uma nota. Nos testes, `GUIA_GH_FIXTURE` aponta um JSON com as respostas do `gh api`.

**Deriva (`--delivery`, D-118).** No modo `pr`, os fatos sao comparados com o que o processo precisa, e cada diferenca vira aviso `deriva: ...` (e `drift` no JSON): sem protecao na base; status da auditoria fora dos checks exigidos (o merge passa sem auditoria); `delivery.audit.statusContext` diferente do que o workflow grava (todo PR trava); agregador de CI nao exigido; `strict` ou `enforce_admins` desligados; squash desligado; auto-merge ligado. `--strict` reprova. No modo `direct`, nada a comparar.

**Hook `commit-msg` (D-115).** Num repositorio git, o `doctor` confere se o hook das travas vai rodar no worktree onde o comando roda: avisa quando `core.hooksPath` aponta para `NUL`/`/dev/null` (hooks desligados), quando a pasta configurada nao tem `commit-msg`, quando o `config.worktree` diverge da config comum (com `extensions.worktreeConfig`), e quando um projeto com travas nao tem hook configurado nem `commit-msg` em `.git/hooks`. Sao avisos; `--strict` reprova.

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
    --file <caminho> [--file <outro>] `
    [--no-commit] `
    [--lock --lock-id <slug>] `
    [--docs-touched <path> ...] `
    [--docs-skip "<motivo>"] `
    [--quality-checked] [--quality-skill <nome> ...] [--quality-finding "<acao>" ...] `
    [--quality-skip "<motivo>"]
```

Marca como `Validada`, sugere `#FINALIZADO` e commita por padrao. Com `--lock`, registra os arquivos da task em `.guia/locks/registry.yaml` sob o slug informado.

**Commit escopado aos arquivos da demanda (D-105).** Com varios chats/agentes na mesma copia de trabalho, o `finish` engolia codigo de outras demandas no commit de encerramento (`git add -A` da arvore + `git commit` sem pathspec selavam o index inteiro); o paliativo era `--no-commit` + staging manual. Agora: (1) o conjunto de arquivos vem **so de `--file`** (ou do que um `ready` anterior acumulou), nunca inferido de `git diff HEAD`; e (2) o commit e **escopado ao pathspec** (`git commit -- <files>`), entao arquivo de outra demanda ja `git add`-ado fica intacto, de fora do commit. Um `finish` que **commita** sem nenhum arquivo de produto declarado e **recusado** com pedido de `--file` (evita commitar so o bookkeeping e deixar o codigo de fora); epicos ficam de fora do gate, e `--no-commit` (dry close) nao exige `--file`. O `--no-commit` deixa de ser necessario como isolamento — sobrevive so como fechamento sem commit.

**Id explicito obrigatorio + guard de status (D-103).** Diferente dos outros verbos, `finish` **nao** cai no `current-task.json` global quando o id e omitido. Esse ponteiro e unico por copia de trabalho: outra sessao/chat na mesma pasta pode te-lo driftado para uma demanda que este chat nunca tocou — e um `finish` sem id ja finalizou a task errada por causa disso (o ponteiro apontava para uma D-NNN em `Backlog` de outro chat). Como o motor nao tem conceito de "chat", quem sabe qual demanda este chat conduz e o agente, que **deve passar o id explicito** (`finish D-NNN`, deduzido da conversa, nao do ponteiro). Sem id, o comando **recusa** e lista as candidatas em `Aguardando validacao`. Alem disso, `finish` so aceita demanda em estado **finalizavel** — `Aguardando validacao` ou `Em desenvolvimento`; `Backlog`/`Planejada` precisam de `start`/`ready` antes, e estados terminais ja foram fechados. O aviso do `status --all` (B-018) continua, mas o gate real do fechamento vive aqui.

**Modo `pr` nao commita; o finish e uma transacao (D-111).** Com `delivery.mode: "pr"`, o `finish` so fecha o estado: o codigo chega a `main` pelo squash do PR. `commitByDefault` e ignorado e `--commit` e recusado. Em qualquer modo, arquivo ignorado pelo `.gitignore` (o `.guia/DEMANDAS.md` local, por exemplo) sai do pathspec do commit em vez de aborta-lo (D-579), e se o commit falhar a demanda volta **inteira** ao estado anterior - status, registro de docs e de qualidade, resumo, arquivos - e a trava criada por `--lock` e desfeita.

**Demanda pela branch no modo `pr` (D-110).** Com `delivery.mode: "pr"`, dentro de uma branch de demanda (`d-NNN-slug`, `e-NNN-slug`) os verbos sem id (`status`, `ready`, `finish` e os demais que usam a demanda atual) resolvem para a `D-NNN` da branch, **antes** do `current-task.json`: a branch e do worktree desta sessao, nao um ponteiro compartilhado. O motor avisa no stderr (`demanda D-NNN resolvida pela branch ...`). Branch sem o padrao, id inexistente, modo `direct` ou arvore principal: tudo como antes. `cancel` continua exigindo id.

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

### Skills por etapa (`--skill-ran`, `--skill-missing`)

`ready`, `finish` (etapa `quality`) e `commit-message` (etapa `commit`) anunciam no stderr a skill da etapa, lida de `skills.<etapa>` no `process.json` (D-114, R12). O agente confere se ela existe na sessao e registra: `--skill-ran <nome>` / `--skill-missing <nome>` (repetiveis) em `ready` e `finish`; no `finish`, `--quality-skill` tambem conta como `ran`. Etapa com `null` registra `disabled`. O portao de qualidade do D-095 continua exigindo `--quality-checked` ou `--quality-skip`; so a lista de candidatas vem da configuracao.

### `ship`

```powershell
.\core\bin\guia.ps1 ship [D-NNN] --body "o porque" [--subject "..."] [--unlock-reason "..."] [--no-changelog "motivo"]
```

Modo `pr` (D-122): leva a demanda do worktree ao PR. Confere, **antes de qualquer efeito**: modo `pr`, branch de demanda, arvore limpa, tabela Pedido -> Teste (`ready --request-test "pedido :: teste"`, obrigatoria salvo `delivery.pr.requestToTest = false`), fragmento de CHANGELOG quando `delivery.changelog.style = fragments` (ou `--no-changelog "motivo"`, que vai para o PR) e o portao `delivery.gate.full` (sem portao, avisa). Depois: empurra a branch, abre ou atualiza o PR (titulo = assunto do commit; corpo = o porque, a tabela, a demanda e `delivery.pr.footer`), grava a mensagem de squash em `.guia/queue/<ID>.msg` (com as marcas `[unlock:]`) e poe a demanda em `Em PR`. A configuracao vem do `process.json` da arvore principal: mudanca de config num PR so vale depois do merge. O `finish` aceita demanda `Em PR`.

### `audit`

```powershell
.\core\bin\guia.ps1 audit [D-NNN] [--skill-missing pr-audit]
.\core\bin\guia.ps1 audit [D-NNN] --report relatorio.md [--approve] [--skill-ran <skill>]
```

Registra a auditoria do PR da demanda (D-123). O motor nao audita: quem audita e a skill de `skills.audit` (padrao `pr-audit`) ou, sem ela, o agente pelo **checklist embutido** (`templates/audit-checklist.md`) - a auditoria e um portao e nao vira aprovacao por falta de skill (R12). Sem `--report`, so le: anuncia a skill, mostra o head, o head no remoto e o patch-id, e com `--skill-missing` imprime o checklist. Com `--report`, comenta o relatorio no PR; com `--approve`, fecha com `<!-- auditoria-aprovada sha=<head> -->` (o `auditoria.yml` grava o status) e grava `audit.auditedSha`, `audit.auditedPatchId` (base do R8) e `audit.via` na demanda. Recusa se o head local nao for o do remoto: o marcador tem de apontar o commit que o GitHub ve.

### `queue` e `approve`

```powershell
.\core\bin\guia.ps1 queue [list] [--json]
.\core\bin\guia.ps1 queue add [D-NNN] [--priority hotfix]
.\core\bin\guia.ps1 queue remove|priority D-NNN [normal|hotfix]
.\core\bin\guia.ps1 queue pause --reason "..." | resume
.\core\bin\guia.ps1 approve D-NNN ... | --all
```

Fila de integracao (D-126, R5). Estado em `.guia/queue.json` (local, na arvore principal), escrito sob trava de arquivo (`O_EXCL`) com gravacao em temporario + troca atomica - varios chats podem enfileirar ao mesmo tempo. `add` exige PR aberto (`ship`), auditoria aprovada **no head atual** (`audit --approve`) e a mensagem de squash; a demanda vai a `Na fila`. A ordem e FIFO com `hotfix` a frente; item com dependencia aberta ou sem aprovacao espera **sem bloquear os de tras**, e a listagem diz o motivo. `approve` e o ok de merge - acao do usuario, pela mesma regra de comportamento do `finish`. `remove` devolve a demanda a `Em PR`. Quem integra e o executor.

```powershell
.\core\bin\guia.ps1 queue run [--once]
```

**Executor (D-127, R5 + R8).** Mecanica pura no motor, sem LLM. Um executor por repositorio: lease em `.guia/queue/executor.lease` com batimento (segundo `run` com lease viva recusa e diz quem roda; lease sem batimento ha `delivery.queue.leaseStaleMinutes`, padrao 10, e assumida). Por item elegivel, na ordem da fila: le o PR (mergeado por fora reconcilia; fechado devolve); head diferente do auditado so segue se o **patch-id** for o mesmo - ai comenta o marcador do head novo com `carry-from=<sha> patch-id=<id>` (R8), senao devolve; `BEHIND` faz `gh pr update-branch --rebase` (conflito devolve; head novo passa de novo pelo patch-id); espera os checks exigidos ate `delivery.queue.ciTimeoutMinutes` (padrao 40; vermelho devolve, estouro deixa esperando); `gh pr merge --squash --match-head-commit` com a mensagem de `.guia/queue/<ID>.msg` e ` (#N)` no assunto; demanda `Integrada`. **Devolver** tira o item da fila, volta a demanda a `Em desenvolvimento` com `queue.returnReason`, e o executor segue para o proximo. `--once` integra no maximo um item. Fila pausada ou congelada: nada roda.

**Depois do merge (D-128).** Para cada PR integrado: remove o worktree da demanda pelo protocolo seguro da D-113 (sem `--force`; nao conseguindo, avisa e mantem); atualiza a arvore principal - limpa, `git pull --ff-only`; suja, so `fetch`, com aviso (nunca pisa no trabalho do dono); e acompanha o CI no commit do squash na main ate `delivery.queue.ciTimeoutMinutes`: o CI do PR prova o PR, o da main prova a combinacao. **Vermelho congela a fila** (`frozenReason`), e nada mais integra em cima da main quebrada; sem resultado no prazo, so avisa. `queue resume` descongela. Rode o executor a partir da arvore principal: ele remove o worktree das demandas, e o Windows nao deixa remover a pasta em que o processo esta.

**PRs da nuvem (D-130).** A sessao na nuvem nao alcanca o `.guia/` do PC: ela faz worktree, commit, push e PR com o rotulo `guia:fila`, e para no PR. O executor, ao iniciar (ou `.\core\bin\guia.ps1 queue import`), traz esses PRs para a fila **sem auditoria**, achando a demanda pela branch `d-NNN-*` (branch sem demanda conhecida so gera aviso; falha do `gh` nessa etapa nao para a fila). Sem auditoria nada integra. No PC: `guia worktree add D-NNN` segue a branch do PR (a partir do que a nuvem empurrou), `ship` grava a mensagem de squash, `audit --approve`, e `queue add` completa o item importado.

### `deps`

```powershell
.\core\bin\guia.ps1 deps [--now] [--json]
```

Os PRs do Dependabot (D-129, R11). Inventaria os PRs abertos do bot e os tria: **bump** = so manifesto ou lockfile, ou so linhas `uses:` de workflow; o resto vai como item comum para a `pr-audit`; rotulo `security` marca prioridade. `--now` cria a demanda do lote (`chore` Planejada, com os PRs em `dependabot.prs`) - uma por vez. O executor cria o lote sozinho quando a fila esvazia (`delivery.dependencies.trigger = on-idle`, padrao). Quem junta as versoes e roda o portao e a skill `pr-bump`, num chat; o lote segue o fluxo normal (ship, audit, fila) e, integrado, o executor fecha cada PR do bot incorporado com link para o lote. PR do bot nunca entra na fila normal nem recebe `update-branch`.

### `changelog`

```powershell
.\core\bin\guia.ps1 changelog add [D-NNN] [--category <Categoria>] [--text "..."]
.\core\bin\guia.ps1 changelog compile [--version X.Y.Z] [--date AAAA-MM-DD]
```

CHANGELOG por fragmentos (D-121). `add` cria `changelog.d/<ID>.<categoria>.md` na arvore de trabalho (o worktree da demanda): categoria pelo kind (`delivery.changelog.categoryByKind`; padrao feature -> Added, bug -> Fixed, chore -> Changed), `--category` para trocar; fragmento existente recusa. O fragmento viaja no PR, e dois PRs nao disputam mais o topo do CHANGELOG. `compile` (na release) junta os fragmentos no `[Unreleased]` - ou, com `--version`, fecha a secao da versao e abre um `[Unreleased]` vazio -, agrupados na ordem do Keep a Changelog e por id numerico, preservando as entradas ja escritas, e apaga os fragmentos.

### `commit-message`

```powershell
.\core\bin\guia.ps1 commit-message [D-NNN] [--body "o porque"] [--unlock-reason "<trava>=<motivo>"] [--subject "..."]
```

Imprime a mensagem de commit da demanda no formato de `delivery.commit.format` (D-112). No modo `pr` o `finish` nao commita, entao e esta mensagem que o agente usa no `git commit -F` e no corpo do squash. No formato `gitmoji-conventional`: header `<emoji> <tipo>(D-NNN): titulo` (feature -> `✨ feat`, bug -> `🐛 fix`, chore -> `🧹 chore`), corpo = `--body`, uma marca `[unlock:<trava>] motivo: ...` por trava que os arquivos declarados tocam e `Co-Authored-By` de `delivery.commit.coAuthor`. A operacao de cada arquivo (adicao, modificacao, delecao) vem do git contra a base (`merge-base` com `origin/<baseBranch>`), nao do disco: arquivo novo conta como adicao. Trava tocada sem motivo recusa (exit 1) citando cada uma; `--unlock-reason` aceita `<trava>=<motivo>` ou um `<motivo>` para todas. Sem id, vale a branch (D-110). O `finish` com commit (modo `direct`) aceita o mesmo `--unlock-reason`.

### `profile`

```powershell
.\core\bin\guia.ps1 profile [--apply] [--name solo-direct|pr-basic|pr-audited] [--json]
```

Propoe o perfil de entrega pelos fatos do `doctor --delivery` (D-119): `solo-direct` (sem remoto GitHub, ou sem CI nem protecao), `pr-basic` (CI no PR, sem auditoria por status) e `pr-audited` (workflow de auditoria). O perfil so preenche chaves que o motor ja usa: `delivery.mode`, `delivery.commit.format` e, no auditado, `delivery.audit.statusContext` (lido do workflow). Sem `--apply`, nada e gravado; com `--apply`, acrescenta ao `process.json` so as chaves ausentes - o que ja esta configurado vence e aparece como mantido. O `doctor --delivery` tambem mostra a proposta.

### `scaffold`

```powershell
.\core\bin\guia.ps1 scaffold auditoria|pr-template|dependabot|ci-ok|protection
```

Andaimes de entrega a partir dos modelos do Guia (`templates/scaffold/`, D-120). `auditoria` cria `.github/workflows/auditoria.yml` (comentario do dono com o marcador grava o status de `delivery.audit.statusContext`); `pr-template` cria `.github/pull_request_template.md` com a tabela Pedido -> Teste; `dependabot` cria `.github/dependabot.yml` agrupado, com o prefixo de commit do formato configurado. **Nunca sobrescreve**: arquivo existente (em qualquer grafia conhecida) recusa sem tocar nada. `ci-ok` e `protection` so **imprimem**: o job agregador com o `needs` dos jobs do workflow principal de PR (jobs de outros workflows vao numa nota, para exigir direto na protecao - `needs` nao enxerga outro arquivo), e os `gh api` de merge e protecao com os checks tirados dos fatos. Mudar o GitHub e acao do dono.

### `worktree`

```powershell
.\core\bin\guia.ps1 worktree add [D-NNN] [--path <rel>] [--branch <nome>]
.\core\bin\guia.ps1 worktree remove [D-NNN] [--force]
```

Cria ou remove o worktree de uma demanda que ja existe (D-113). `add` segue `delivery.worktree`: caminho e branch pelos modelos, a partir de `from` (busca a base no `origin` antes), copia os `envFiles` e cria as `junctions`, registrando tudo na demanda (`WORKTREE_PATH=`, `WORKTREE_BRANCH=`). `remove` desfaz as juncoes registradas **antes** do `git worktree remove` e **recusa** se sobrar qualquer link no worktree - uma remocao que atravessa juncao apaga o destino na principal (D-880 no gerador-cortes). Sem `--force`, worktree com mudanca nao commitada fica, com a mensagem do git. No modo `pr`, o `finish` remove o worktree da demanda (se `removeOnFinish`) do mesmo jeito, sem `--force`, e so avisa se nao conseguir. Sem id, vale a branch (D-110).

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

**Id explicito obrigatorio (D-104).** Como o `finish` (D-103), `cancel` **nao** cai no `current-task.json` global quando o id e omitido — `cancel` e terminal (`Cancelada`) e irreversivel, e o ponteiro global drifta entre sessoes/chats concorrentes na mesma pasta, entao um `cancel` sem id podia cancelar uma demanda que este chat nunca tocou. O agente **deve passar o id explicito** (`cancel D-NNN`, deduzido da conversa). Sem id, o comando **recusa** e lista as candidatas abertas (nao-terminais) — universo mais amplo que o do `finish`, ja que `cancel` vale de qualquer estado nao-terminal (`Backlog`/`Planejada`/`Em desenvolvimento`/`Aguardando validacao`/`Bloqueada`). A resolucao compartilhada vive em `_resolve_terminal_target` (reusada por `finish` e `cancel`).

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
