# AI Process Pack

Processo portavel para Codex, Claude, Antigravity e outros agentes. O objetivo e transformar pedidos soltos em demandas rastreaveis, com backlog, status, validacao e lock, usando script deterministico em vez de depender da memoria do agente.

## Ideia central

- Skill = interface conversacional.
- Script = fonte de verdade e automacao.
- `.ai/*.json` = estado legivel por programas.
- `FEATURES.md` = historico legivel por humano.
- `features/registry.yaml` = lock de arquivos homologados.
- Hooks = guarda-corpo opcional para lembrar ou bloquear desvios.

## Comandos

```powershell
.\scripts\ai.ps1 feature "Titulo curto" --context "Motivo e escopo"
.\scripts\ai.ps1 issue "Bug observado" --context "Sintoma e impacto"
.\scripts\ai.ps1 backlog add "Ideia futura" --context "Quando pode ser util"
.\scripts\ai.ps1 backlog list
.\scripts\ai.ps1 promote B-001 --kind feature --assessment "Claro e acionavel" --plan "Inspecionar area afetada"
.\scripts\ai.ps1 status
.\scripts\ai.ps1 ready F-016 --file scripts/ai.py --summary "CLI criado" --validation "python scripts/ai.py doctor"
.\scripts\ai.ps1 finish F-016 --lock --lock-id ai-process-pack
```

Aliases conversacionais esperados:

- `/feature`: cria `F-NNN`.
- `/issue`: cria `I-NNN`.
- `/backlog`: controla ideias futuras.
- `/promote B-NNN`: avalia e promove backlog para feature/issue depois de plano aprovado.
- `/ready`: move para `Aguardando validacao`.
- `/finish`: encerra demanda ja validada, sugere `#FINALIZADO` e commita por padrao.
- `/status`: mostra tarefa atual e titulo sugerido.

## Estrutura

```text
.ai/
  process.json       Configuracao do pacote neste projeto.
  tasks.json         Fonte programatica das demandas.
  backlog.json       Itens futuros, ainda nao iniciados.
  current-task.json  Demanda ativa.
  chat-title.txt     Ultimo nome sugerido para o chat.
  reports/           Relatorios gerados por ready/finish.
scripts/
  ai.py              CLI portavel, Python puro.
  ai.ps1             Wrapper Windows que localiza Python.
.agents/skills/
  ai-process/        Skill para Codex e Antigravity.
  feature/           Shim para `$feature` no Codex.
  promote/           Shim para `$promote` no Codex.
  finish/            Shim para `$finish` no Codex.
.claude/skills/
  ai-process/        Skill espelhada para Claude.
.claude/commands/
  feature.md         Slash commands finos do Claude.
```

## Fluxo recomendado

1. Comece com `/feature`, `/issue` ou `/backlog add`.
2. O script cria o ID, atualiza `.ai/tasks.json`, `.ai/current-task.json` e `FEATURES.md`.
3. O script sempre imprime `NOME DO CHAT: ...` e grava `.ai/chat-title.txt`.
4. O agente repete esse nome no chat e executa a renomeacao real quando a ferramenta expuser API ou comando de sessao.
5. Durante a implementacao, o agente registra arquivos e validacoes.
6. `/ready F-016` move para `Aguardando validacao`.
7. Paulo testa em uso real.
8. `/finish F-016` marca `Validada`, sugere `F-016 - #FINALIZADO - ...` e commita por padrao.
9. Se Paulo quiser travar, use `finish --lock --lock-id <slug>`.

`validate` ainda existe como compatibilidade, mas nao e o fluxo recomendado.

## Promote

`/promote B-NNN` nao deve criar tarefa automaticamente sem raciocinio antes.

Fluxo obrigatorio:

1. Ler o item em `.ai/backlog.json`.
2. Classificar como `feature` ou `issue`.
3. Avaliar se titulo/contexto sao suficientes.
4. Se faltar informacao, perguntar antes de criar demanda.
5. Propor plano curto de execucao.
6. Confrontar riscos: locks provaveis, funcionalidades impactadas e alternativas.
7. Perguntar se deve usar worktree.
8. Com OK do Paulo, rodar `scripts/ai.ps1 promote`.

Exemplo sem worktree:

```powershell
.\scripts\ai.ps1 promote B-019 --kind issue --assessment "Regressao de agendamento" --plan "Inspecionar servico de publicacao em massa"
```

Exemplo com worktree:

```powershell
.\scripts\ai.ps1 promote B-019 --kind issue --worktree --assessment "Regressao de agendamento" --plan "Criar teste de intervalo antes do fix"
```

Quando uma task promovida com `--worktree` for finalizada, `finish` tenta remover a worktree registrada. O caminho padrao e `.claude/worktrees/<task-slug>` porque essa pasta ja e ignorada neste repo.

## Arquivos travados

Antes de editar qualquer arquivo, confira `features/registry.yaml`.

Se o arquivo estiver travado, o agente deve explicar antes de pedir unlock:

- qual `id` de lock bloqueia o arquivo;
- qual funcionalidade esta protegida pela descricao do lock;
- por que a mudanca precisa tocar esse arquivo;
- impacto esperado na funcionalidade protegida;
- risco de regressao;
- alternativa sem mexer no arquivo travado, se existir.

So depois disso o agente pede autorizacao explicita.

### Tipos de Lock

Cada lock pode limitar quais operacoes bloqueia:

```yaml
- id: exemplo-total
  description: Protege feature inteira
  operations: [add, modify, delete, rename]
  files:
    - frontend/src/foo.tsx

- id: exemplo-so-remocao
  description: Nao remover contrato publico
  operations: [delete, rename]
  files:
    - backend/app/domain/contrato.py
```

Operacoes:

- `add`: criacao/adicao de arquivo.
- `modify`: alteracao de arquivo existente.
- `delete`: remocao.
- `rename`: renome/movimento.

Locks antigos sem `operations` continuam equivalendo a lock total.

`features/lock-ignore.txt` lista arquivos que nunca devem ser travados. Hoje inclui `.gitignore` e o proprio `features/lock-ignore.txt`.

Existe lock global `adicoes-exigem-autorizacao` com `operations: [add]` e `files: ["*"]`. Resultado: qualquer arquivo novo exige autorizacao, exceto caminhos em `features/lock-ignore.txt`.

## Renomear chat

O script imprime sempre um titulo sugerido:

```text
F-016 - #DEV - Titulo
F-016 - #VALIDACAO - Titulo
F-016 - #FINALIZADO - Titulo
```

Regra operacional: depois de qualquer `feature`, `issue`, `ready`, `finish`, `validate` ou `status`, o agente deve repetir no chat a linha `NOME DO CHAT: ...`.

Isso nao basta para renomear a UI. Sempre que a ferramenta expuser uma API ou comando de thread/sessao, o agente deve executar esse passo explicitamente.

Suporte por ferramenta:

- Codex App: procurar as ferramentas de thread quando necessario, chamar `codex_app.list_threads` para achar o id do chat atual e depois chamar `codex_app.set_thread_title` com exatamente o titulo impresso em `NOME DO CHAT: ...`. Para identificar o chat atual, usar sinais como `status: active`, `cwd`, `preview` da mensagem corrente e o `updatedAt` mais recente. Apenas reportar `NOME DO CHAT` na conversa nao renomeia a UI.
- Claude Code: usar `/rename <titulo>` durante a sessao quando o comando estiver disponivel, ou iniciar uma sessao ja nomeada com `claude -n <titulo>` quando essa flag estiver disponivel. Claude nao usa `codex_app.*`; se nao houver API/comando de sessao acessivel ao agente, ele deve repetir `NOME DO CHAT: ...` para o humano aplicar.
- Antigravity CLI: usar `/rename <titulo>`.
- Codex CLI/TUI: versoes recentes possuem `/rename` para a thread atual. Em superficies onde o agente nao consegue invocar slash command da propria conversa, ele deve imprimir o titulo para o humano aplicar.

Importante: editar arquivos internos de historico (`~/.codex`, `~/.claude`, etc.) nao e o caminho padrao. Esses formatos sao privados, podem mudar e podem nao atualizar a UI ativa.

## Hooks

Hooks sao opcionais. Eles nao substituem o script. Eles apenas protegem o processo.

Bons usos:

- `UserPromptSubmit`: se o pedido parece feature/issue e nao ha task ativa, lembrar de rodar `/feature` ou `/issue`.
- `PreToolUse`: antes de editar arquivo, checar `features/registry.yaml`.
- `PostToolUse`: apos editar, sugerir registrar arquivos na demanda atual.
- `Stop`: antes do agente finalizar, avisar se houve mudanca sem `/ready` ou sem `finish`, conforme o estado.

Use hooks primeiro em modo aviso. So depois torne bloqueante.

## Plugin ou repo?

Plugin e viavel e provavelmente e o destino ideal quando o processo estabilizar. Ele empacotaria skills, hooks, comandos e instalador. Para agora, este repo usa um pack local porque e mais facil iterar e debugar.

Caminho sugerido:

1. Estabilizar aqui.
2. Extrair para um repo Git, por exemplo `ai-process-pack`.
3. Criar instalador que copie `scripts`, `.ai` base, skills e comandos.
4. Opcionalmente transformar em plugin para Codex/Antigravity quando a API de plugin for o melhor encaixe.

## Portar para outro projeto

Copie estes caminhos:

```text
scripts/ai.py
scripts/ai.ps1
.ai/process.json
.ai/chat-title.txt
.agents/skills/ai-process/SKILL.md
.agents/skills/feature/SKILL.md
.agents/skills/promote/SKILL.md
.agents/skills/finish/SKILL.md
.claude/skills/ai-process/SKILL.md
.claude/commands/
docs/AI_PROCESS.md
```

No novo projeto:

```powershell
.\scripts\ai.ps1 init --project-name "nome-do-projeto"
.\scripts\ai.ps1 doctor
```

Depois ajuste `.ai/process.json` para comandos de teste e politica de lock do projeto.
