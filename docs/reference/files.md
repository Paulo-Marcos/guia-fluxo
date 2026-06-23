# Reference: arquivos do processo

## Layout

```text
.guia/
  process.json       Configuracao do pacote neste projeto.
  tasks.json         Fonte programatica das demandas.
  backlog.json       Itens futuros, ainda nao iniciados.
  current-task.json  Demanda ativa.
  demand-title.txt   Titulo da demanda corrente (pointer estavel; rename do chat e opcional).
  docs-map.yaml      Opcional. Declaracao dos docs vivos para o hook do `finish`.
  reports/           Relatorios gerados por ready/finish.
  DEMANDAS.md        Historico legivel por humano. Espelha tasks.json em prosa.

core/
  src/guia.py                CLI portavel, Python puro.
  bin/guia.ps1               Wrapper Windows que localiza Python e invoca core/src/guia.py.
  build/render-skills.py   Regenera plugins/guia/commands/ e plugins/guia/.agents/skills/ a partir do manifest.
  manifest/manifest.yaml   Fonte unica das skills (Codex, Claude, Antigravity).
  lock/check-lock.py       CLI de locks: list, lock, unlock, audit, check.
  hooks/commit-msg         Hook que valida marcas [unlock:<id>] (`git config core.hooksPath core/hooks`).
  templates/               Snippets enviados pro consumidor durante install.

plugins/guia/
  .claude-plugin/plugin.json       Manifest oficial Claude Code (name=guia). Define namespace dos skills.
  .claude-plugin/marketplace.json  Catalogo do marketplace local (source `../`, plugin root = plugins/guia/).
  commands/<verbo>.md              Saida do render para Claude Code (plugin command -> /guia:<verbo>). NAO editar a mao.
  .agents/skills/<verbo>/SKILL.md  Saida do render para Codex/Antigravity (convencao AGENTS.md). NAO editar a mao.

.guia/locks/
  registry.yaml      Fonte da verdade da lista de travas.
  lock-ignore.txt    Arquivos que nunca devem ser travados.
```

## `.guia/process.json`

Configuracao por projeto. Inclui:

- nome do projeto;
- comandos de teste e validacao;
- politica de lock (autovalidacao, etc.).

## `.guia/tasks.json`

Lista todas as demandas (features, bugs e chores) com status. Fonte programatica - leia daqui em vez de fazer parse de `.guia/DEMANDAS.md`.

## `.guia/current-task.json`

A demanda ativa no momento. Contem `taskId`, `status`, `title`, `demandTitle`.

Exemplo:

```json
{
  "taskId": "D-016",
  "status": "Em desenvolvimento",
  "title": "Adicionar comando de export",
  "demandTitle": "D-016 ✨ - #DEV - Adicionar comando de export"
}
```

## `.guia/backlog.json`

Itens futuros (`B-NNN`). Cada entrada tem id, titulo e contexto. Promovidos via `/promote` viram feature, bug ou chore.

## `.guia/docs-map.yaml`

Opcional. Declara os documentos vivos do projeto (README, CHANGELOG, docs/reference, ADRs, etc.) e quando cada um deve ser considerado para atualizacao. Quando presente, o `guia.py finish` bloqueia o fechamento ate o agente registrar o que fez com cada candidato. Quando ausente, o hook vira no-op com aviso amigavel.

Schema completo em [`docs-map.md`](docs-map.md). Receita de uso em [`docs/how-to/manter-docs-atualizados.md`](../how-to/manter-docs-atualizados.md).

## `.guia/reports/`

Relatorios gerados por `ready` e `finish`. Nome no formato `<task-id>-<acao>-<timestamp>.md`. Servem como historico granular alem do `.guia/DEMANDAS.md`.

## `.guia/DEMANDAS.md`

Historico humano-legivel. Cada secao tem:

- ID e titulo;
- status;
- origem e tipo;
- contexto;
- arquivos modificados;
- o que foi feito;
- validacoes feitas;
- validacoes pendentes.

O script reescreve este arquivo a cada operacao. Nao edite a mao - voce sera sobrescrito.

## `.guia/locks/lock-ignore.txt`

Lista de paths/globs que **nunca** devem ser travados. Hoje inclui `.gitignore` e o proprio `.guia/locks/lock-ignore.txt`. Existe para evitar lock global acidental em arquivos triviais.

## `plugins/guia/.claude-plugin/plugin.json`

Manifest oficial do plugin Claude Code (spec: <https://code.claude.com/docs/en/plugins>). Define `name` (`ai`, vira namespace dos atalhos: `/guia:feature`, `/guia:bug`, ...), `description`, `version` e metadados (author, homepage, repository, license). Mudar so para bump de versao ou ajuste de metadados.

## `core/manifest/manifest.yaml`

Fonte unica das skills do pack. Estrutura por verbo + targets (`agent_skill` para Codex/Antigravity, `claude_command` para Claude Code). Editado a mao; consumido pelo `core/build/render-skills.py`.

## `plugins/guia/commands/<verbo>.md`

Saida do `core/build/render-skills.py` para Claude Code (plugin **command**, surge namespaced como `/guia:<verbo>` - plugin skills surgiriam bare). Cada verbo do manifest produz um arquivo flat. Nao editar manualmente. Edite `core/manifest/manifest.yaml` e rode `render-skills.py`.

## `plugins/guia/.agents/skills/<verbo>/SKILL.md`

Saida do `core/build/render-skills.py` para Codex + Antigravity (convencao AGENTS.md cross-tool, <https://agents.md/>). Cada verbo do manifest produz um arquivo. Nao editar manualmente. Edite `core/manifest/manifest.yaml` e rode `render-skills.py`.

Decisao arquitetural do layout em [`../adr/0006-plugin-oficial-claude-code.md`](../adr/0006-plugin-oficial-claude-code.md).
