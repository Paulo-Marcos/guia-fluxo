# Reference: suporte de renomeacao de chat por ferramenta

Cada comando do CLI imprime `NOME DO CHAT: ...`. Como aplicar isso na UI varia por ferramenta.

## Claude Code

- Comando: `/rename <titulo>` durante a sessao quando disponivel.
- Inicio de sessao: `claude -n <titulo>` quando essa flag estiver disponivel.
- Claude **nao** usa `codex_app.*`. Se nao houver API/comando de sessao acessivel, repita `NOME DO CHAT: ...` para o humano aplicar.

## Codex App

- Listar threads: `codex_app.list_threads`.
- Renomear: `codex_app.set_thread_title` com **exatamente** o titulo impresso em `NOME DO CHAT: ...`.
- Identificar a thread atual: combine sinais como `status: active`, `cwd` correspondente, `preview` da mensagem corrente e `updatedAt` mais recente.

**Importante:** apenas reportar `NOME DO CHAT` na conversa **nao renomeia** a UI. Sempre faca a chamada da API quando a ferramenta expuser.

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
<TASK-ID> - #<FASE> - <TITULO>
```

Fases:

- `#DEV` - em desenvolvimento.
- `#VALIDACAO` - aguardando validacao (`ready`).
- `#FINALIZADO` - validado (`finish`).

Exemplos:

```text
F-016 - #DEV - Adicionar comando de export
F-016 - #VALIDACAO - Adicionar comando de export
F-016 - #FINALIZADO - Adicionar comando de export
```
