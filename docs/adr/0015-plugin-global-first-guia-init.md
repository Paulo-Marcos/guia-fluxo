# ADR-0015: Plugin global-first + `/guia:init`

- **Status:** Aceita
- **Data:** 2026-06-17

## Contexto

O ADR-0014 (D-075) tornou o caminho Claude Code autossuficiente: o motor viaja
dentro do plugin (`${CLAUDE_PLUGIN_ROOT}/bin/guia.py`), a raiz do projeto vem do
CWD e um auto-init cria `.guia/` no primeiro comando — sem clone, sem `init`
manual. Faltava convergir o layout e a experiencia de adocao para o modelo
"plugin global, projeto so com estado", espelhando a estrutura do
[openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc): nele o
`marketplace.json` fica na raiz apontando para um subdir `plugins/<nome>/`
auto-contido, os scripts rodam sempre de `${CLAUDE_PLUGIN_ROOT}` e **nada** e
copiado para o projeto do cliente.

Dois pontos ficaram em aberto no guia-fluxo:

1. O setup de locks/hook (registry, `lock-ignore`, `commit-msg`, `hooksPath`) so
   existia via `install.ps1`/`install.sh`, que copiam o pack inteiro para
   `.guia-fluxo/` no consumidor. Um consumidor Claude no-clone nao tinha como
   ligar os locks.
2. O diretorio de build se chamava `dist/` (sugere "descartavel"), divergindo da
   convencao `plugins/<nome>/` do codex-plugin-cc.

Restricao herdada: as skills sao **geradas** de `core/manifest/` por
`core/build/render-skills.py`, entao fonte (`core/`) e saida (build) precisam
continuar separadas — nao da pra ter um diretorio de plugin escrito a mao como o
codex-plugin-cc (cujos scripts `.mjs` nao tem etapa de build).

O suporte cross-tool (Codex/Antigravity via target `agent_skill`,
`.agents/skills/`, `install.*`, layout `.guia-fluxo/`) tem um gap conhecido (as
skills do agente mandam rodar `core/bin/guia.ps1`, que so existe num clone) e foi
deliberadamente **adiado** para uma demanda separada — esta ADR nao o resolve nem
o remove.

## Decisao

Convergir para plugin-global-first em tres movimentos, preservando o cross-tool
intacto:

1. **`/guia:init` (verbo novo).** O `init` passa a, alem de semear `.guia/`,
   deployar os templates por-projeto a partir do `templates/` do plugin
   (`features/registry.yaml`, `features/lock-ignore.txt`, `.githooks/commit-msg`)
   e configurar `git core.hooksPath`. Idempotente e nunca clobbera estado
   existente. `--no-locks` faz so o seed de `.guia/`. Continua opcional: o
   auto-init do D-075 cobre o `.guia/`; `init` e o opt-in para os locks.
2. **`dist/` -> `plugins/guia/`.** Renomeacao do diretorio de build para espelhar
   o codex-plugin-cc. O `marketplace.json` da raiz e o `.claude/settings.json`
   passam a apontar para `./plugins/guia`. O build (`core/` -> render) e mantido.
3. **Locks funcionais no consumidor.** `lock_api.REPO_ROOT` passa a honrar
   `GUIA_PROJECT_ROOT` (aditivo; default inalterado), `check-lock.py` passa a ser
   embarcado no `bin/` do plugin, e o `commit-msg` vira robusto: descobre o
   validador em `core/lock/` (repo-mae) ou em `${CLAUDE_PLUGIN_ROOT}/bin/`
   (consumidor, dentro de uma sessao Claude) e degrada com aviso (exit 0) se nao
   achar nenhum — em vez de quebrar.
4. **Target Claude = `commands/`, nao `skills/`.** O `render-skills.py` passa a
   gerar `plugins/guia/commands/<verbo>.md` (plugin *command*, frontmatter so com
   `description`, nome derivado do stem) em vez de `skills/<verbo>/SKILL.md`.
   Motivo (validado em uso real): plugin *skills* surgem **bare** no menu de
   slash (`/init`, `/feature`) com um rotulo `(guia)` — colidindo com nativos
   como `/init` — enquanto plugin *commands* surgem **namespaced** (`/guia:init`),
   como no codex-plugin-cc. Comandos tambem auto-disparam por `description`, entao
   o auto-trigger do modelo e preservado. O target `agent_skill`
   (Codex/Antigravity, `.agents/skills/`) **continua** como Agent Skill.

## Consequencias

- + Um consumidor Claude no-clone liga locks + hook com um unico `/guia:init`,
  sem `install.*` e sem copia do motor no projeto.
- + O layout `plugins/guia/` alinha com a convencao do codex-plugin-cc e deixa o
  nome do diretorio honesto ("o plugin", nao "build descartavel").
- + Locks passam a valer no consumidor no fluxo principal (o agente commitando
  dentro de uma sessao Claude, com `${CLAUDE_PLUGIN_ROOT}` setado), porque o
  `commit-msg` acha o `check-lock.py` do plugin e mira o registry do projeto via
  `GUIA_PROJECT_ROOT`.
- + `init` idempotente e no-clobber: seguro rodar em projeto ja inicializado.
- + Os verbos surgem **namespaced** como `/guia:<verbo>` no Claude (plugin
  commands), sem colidir com built-ins (`/init`) nem poluir o menu com nomes
  bare.
- - Migrar `skills/` -> `commands/` churnou `render-skills.py` (target
  `claude_command`, output flat sem `name:`), o manifest (key `claude_skill` ->
  `claude_command`) e os testes que liam `plugins/guia/skills/`. Mitigado pela
  suite verde.
- - Commit feito **fora** de uma sessao Claude num consumidor puro nao tem
  `${CLAUDE_PLUGIN_ROOT}` setado: o hook degrada (avisa e libera o commit sem
  checar lock). Endurecer esse caminho depende do redesenho de deploy/cross-tool,
  adiado.
- - A renomeacao `dist/` -> `plugins/guia/` churna `render-skills.py`,
  `settings.json`, os dois `marketplace.json`, o `doctor` e os testes que
  referenciavam `dist/`. Mitigado por `render --check` e a suite verde.
- - O cross-tool (Codex/Antigravity) continua com o gap de invocacao do D-075
  (skills do agente apontam para `core/bin/guia.ps1`); esta ADR nao o fecha.

## Alternativas consideradas

- **Dropar o cross-tool e virar Claude-plugin-only** (espelho 1:1 do
  codex-plugin-cc, que e Claude-only). Simplificaria bastante (remover target
  `agent_skill`, `.agents/skills/`, `install.*`, `.guia-fluxo/`,
  `test_install.py`). Rejeitada agora: o dono quer preservar o cross-tool no core
  e trata-lo numa demanda separada.
- **Copiar `check-lock.py` + `lock_api.py` para `.githooks/` no consumidor** para
  o hook ser 100% autossuficiente. Rejeitada: reintroduz copias do motor no
  projeto (exatamente o que o plugin-global-first elimina) e elas viram stale a
  cada update do plugin.
- **Embutir o caminho do plugin no hook commitado.** Rejeitada: caminho absoluto
  especifico de maquina/versao no controle de versao quebra para o time e a cada
  update.

## Links

- ADR-0014 (`docs/adr/0014-plugin-autossuficiente-claude-plugin-root.md`) — base
  que esta ADR estende.
- ADR-0006 (`docs/adr/0006-plugin-oficial-claude-code.md`) — layout de plugin
  oficial e o marketplace local de dogfood.
- Referencia de estrutura: https://github.com/openai/codex-plugin-cc
- How-to: `docs/how-to/instalar-em-outro-projeto.md`.
