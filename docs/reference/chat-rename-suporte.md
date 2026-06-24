# Reference: suporte de renomeacao de chat por ferramenta

Cada comando do CLI imprime `NOME DA DEMANDA: ...` — info da demanda corrente, **nao** um titulo de chat. Renomear o chat e **opcional** ([ADR-0018](../adr/0018-nome-da-demanda-chat-diferente-de-demanda.md)); so vale quando uma demanda mapeia limpo para o chat (um chat com varias demandas — epico D-049 — nao deve ser renomeado para uma so). Como aplicar a renomeacao na UI varia por ferramenta.

## Claude Code

- Surrogate confiavel (na sessao, pelo agente): `mark_chapter` (`mcp__ccd_session__mark_chapter`) com o titulo da demanda — coloca divisor + entrada na ToC. **Nao** renomeia de verdade no picker/titulo do terminal, mas cobre a navegacao.
- Renomeacao real, na sessao, **pelo humano**: `/rename <titulo>` (slash command digitado; o agente nao consegue dispara-lo programaticamente).
- Inicio de sessao: `claude -n <titulo>` — define o nome **no lancamento** (e o escopo da **D-048**, nao da renomeacao de sessao viva).
- Helper fino: `core/bin/guia-rename.ps1` / `core/bin/guia-rename` le `.guia/demand-title.txt`, copia o titulo para o clipboard e imprime destacado — voce so da `/rename` + cola. Ver [how-to/renomear-chat.md](../how-to/renomear-chat.md).
- Claude **nao** usa `codex_app.*`. Se nao houver superficie acessivel, basta repetir `NOME DA DEMANDA: ...` para o humano.

> **Viabilidade (verificado na D-057):** **nao existe** mecanismo para um processo externo renomear uma sessao Claude Code **ja aberta** — sem flag de CLI, arquivo observado, IPC ou MCP ([claude-code#67680](https://github.com/anthropics/claude-code/issues/67680) pede exatamente isso, ainda aberta). Por isso a D-057 nao "aciona" rename nenhum: o essencial ja e o `mark_chapter` (in-session), e o helper acima so facilita o `/rename` manual via clipboard.

## Codex App

- Listar threads: `codex_app.list_threads`.
- Renomear: `codex_app.set_thread_title` com **exatamente** o titulo impresso em `NOME DA DEMANDA: ...`.
- Identificar a thread atual: combine sinais como `status: active`, `cwd` correspondente, `preview` da mensagem corrente e `updatedAt` mais recente.

**Importante:** o print de `NOME DA DEMANDA` **nao renomeia** a UI — e info da demanda, nao do chat. A renomeacao e um passo opcional; faca a chamada da API so quando ajudar a navegacao.

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
- `#FINALIZADO` - validado (`finish`).

Exemplos:

```text
D-016 ✨ - #DEV - Adicionar comando de export
D-016 ✨ - #VALIDACAO - Adicionar comando de export
D-016 ✨ - #FINALIZADO - Adicionar comando de export
```
