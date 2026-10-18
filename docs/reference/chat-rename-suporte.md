# Reference: suporte de renomeacao de chat por ferramenta

Cada comando do CLI imprime `NOME DA DEMANDA: ...`. Desde a [ADR-0020](../adr/0020-chat-nomeado-pela-demanda-um-chat-por-demanda.md), cada demanda tem o seu chat e essa linha e o titulo dele, atualizado a cada etapa. Como aplicar varia por ferramenta.

## Claude Code

- **Rename real, pelo agente (desktop):** `mcp__ccd_session_mgmt__set_session_title` com `session_id: "self"` e a linha exata de `NOME DA DEMANDA`. Tool adiada: carregue com ToolSearch `select:mcp__ccd_session_mgmt__set_session_title`. Pede aprovacao quando o titulo atual foi dado pelo dono; recusa em sessao desatendida.
- **Chat novo por demanda (desktop):** `mcp__ccd_session__start_session` com `title` = `NOME DA DEMANDA`, `model`/`effort` do `triage D-NNN --json` e brief `start D-NNN`. A sessao nasce relacionada a de origem. So desce de modelo: recomendacao acima do chat atual e avisada ao dono.
- **Sem a tool:** `mark_chapter` (`mcp__ccd_session__mark_chapter`, divisor + ToC); `/rename <titulo>` digitado pelo humano; `claude -n <titulo>` no lancamento (D-048); helper `core/bin/guia-rename.ps1` / `core/bin/guia-rename` (clipboard). Ver [how-to/renomear-chat.md](../how-to/renomear-chat.md).
- Claude **nao** usa `codex_app.*`.

> **Historico (D-057):** quando a ADR-0018 foi escrita nao havia como renomear uma sessao ja aberta ([claude-code#67680](https://github.com/anthropics/claude-code/issues/67680)). O Claude Code desktop passou a expor `set_session_title` - verificado na D-185. Processo **externo** ainda nao renomeia; quem renomeia e o agente dentro da sessao.

## Codex App

- Listar threads: `codex_app.list_threads`.
- Renomear: `codex_app.set_thread_title` com **exatamente** o titulo impresso em `NOME DA DEMANDA: ...`.
- Identificar a thread atual: combine sinais como `status: active`, `cwd` correspondente, `preview` da mensagem corrente e `updatedAt` mais recente.

**Importante:** o print de `NOME DA DEMANDA` sozinho **nao renomeia** a UI; o agente faz a chamada da API.

## Codex CLI / TUI

- `/rename` para a thread atual (versoes recentes).
- Em superficies onde o agente nao consegue invocar slash command da propria conversa, imprime o titulo para o humano aplicar.

## Antigravity CLI

- `/rename <titulo>`.

## O que NAO fazer

Editar arquivos internos de historico (`~/.codex`, `~/.claude`, etc.) **nao** e o caminho padrao:

- formatos privados;
- podem mudar entre versoes;
- podem nao atualizar a UI ativa.

## Formato do titulo

```text
<TASK-ID> <emoji> - #<FASE> - <TITULO>
```

Fases:

- `#DEV` - em desenvolvimento.
- `#VALIDACAO` - aguardando validacao (`ready`).
- `#PR` / `#FILA` / `#INTEGRADA` - entrega por PR.
- `#FINALIZADO` - validado (`finish`).
- Acima de `manual`, o nivel de autonomia vem junto: `#DEV·pilot`.

Exemplos:

```text
D-016 ✨ - #DEV - Adicionar comando de export
D-016 ✨ - #VALIDACAO - Adicionar comando de export
D-016 ✨ - #FINALIZADO - Adicionar comando de export
```
