# Reference: arquivos do processo

## Layout

```text
.ai/
  process.json       Configuracao do pacote neste projeto.
  tasks.json         Fonte programatica das demandas.
  backlog.json       Itens futuros, ainda nao iniciados.
  current-task.json  Demanda ativa.
  chat-title.txt     Ultimo nome sugerido para o chat.
  docs-map.yaml      Opcional. Declaracao dos docs vivos para o hook do `finish`.
  reports/           Relatorios gerados por ready/finish.

FEATURES.md          Historico legivel por humano. Espelha tasks.json em prosa.

scripts/
  ai.py              CLI portavel, Python puro.
  ai.ps1             Wrapper Windows que localiza Python.
  render-skills.py   Regenera skills/generated/ a partir do manifest.

bin/
  check-lock.py      CLI de locks: list, lock, unlock, audit, check.

features/
  registry.yaml      Fonte da verdade da lista de travas.
  lock-ignore.txt    Arquivos que nunca devem ser travados.

skills/
  manifest.yaml      Fonte unica das skills (Codex, Claude, Antigravity).
  generated/         Saida do render. NAO editar manualmente.
    .agents/skills/  Skills para Codex e Antigravity.
    .claude/skills/  Skills para Claude Code (com slash commands).

.githooks/
  commit-msg         Hook que valida marcas [unlock:<id>].
```

## `.ai/process.json`

Configuracao por projeto. Inclui:

- nome do projeto;
- comandos de teste e validacao;
- politica de lock (autovalidacao, etc.).

## `.ai/tasks.json`

Lista todas as demandas (features e issues) com status. Fonte programatica - leia daqui em vez de fazer parse de `FEATURES.md`.

## `.ai/current-task.json`

A demanda ativa no momento. Contem `taskId`, `status`, `title`, `chatTitle`.

Exemplo:

```json
{
  "taskId": "F-016",
  "status": "Em desenvolvimento",
  "title": "Adicionar comando de export",
  "chatTitle": "F-016 - #DEV - Adicionar comando de export"
}
```

## `.ai/backlog.json`

Itens futuros (`B-NNN`). Cada entrada tem id, titulo e contexto. Promovidos via `/promote` viram feature ou issue.

## `.ai/docs-map.yaml`

Opcional. Declara os documentos vivos do projeto (README, CHANGELOG, docs/reference, ADRs, etc.) e quando cada um deve ser considerado para atualizacao. Quando presente, o `ai.py finish` bloqueia o fechamento ate o agente registrar o que fez com cada candidato. Quando ausente, o hook vira no-op com aviso amigavel.

Schema completo em [`docs-map.md`](docs-map.md). Receita de uso em [`docs/how-to/manter-docs-atualizados.md`](../how-to/manter-docs-atualizados.md).

## `.ai/reports/`

Relatorios gerados por `ready` e `finish`. Nome no formato `<task-id>-<acao>-<timestamp>.md`. Servem como historico granular alem do `FEATURES.md`.

## `FEATURES.md`

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

## `features/lock-ignore.txt`

Lista de paths/globs que **nunca** devem ser travados. Hoje inclui `.gitignore` e o proprio `features/lock-ignore.txt`. Existe para evitar lock global acidental em arquivos triviais.

## `skills/generated/`

Saida do `scripts/render-skills.py`. Cada subdiretorio espelha o destino final no projeto consumidor:

- `skills/generated/.agents/skills/<verbo>/SKILL.md` -> `.agents/skills/<verbo>/SKILL.md` (Codex e Antigravity).
- `skills/generated/.claude/skills/<verbo>/SKILL.md` -> `.claude/skills/<verbo>/SKILL.md` (Claude Code).

Nao editar manualmente. Edite `skills/manifest.yaml` e rode `render-skills.py`.
