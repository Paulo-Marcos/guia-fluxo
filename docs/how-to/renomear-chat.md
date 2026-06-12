# Como renomear o chat

Todo comando do CLI (`feature`, `bug`, `chore`, `ready`, `finish`, `status`) imprime um titulo sugerido no formato:

```text
F-016 - #DEV - Titulo
F-016 - #VALIDACAO - Titulo
F-016 - #FINALIZADO - Titulo
```

## Regra operacional

Depois de qualquer um desses comandos, o agente deve **repetir no chat** a linha `NOME DO CHAT: ...`.

Isso nao basta para renomear a UI. Sempre que a ferramenta expuser API ou comando de thread/sessao, o agente deve executar o passo de renomeacao real.

## Aplicar a renomeacao na UI

A forma muda por ferramenta. Ver [reference/chat-rename-suporte.md](../reference/chat-rename-suporte.md) para a lista completa.

Resumo rapido:

- **Claude Code**: `/rename <titulo>` durante a sessao, ou iniciar com `claude -n <titulo>`.
- **Codex App**: `codex_app.set_thread_title` com o titulo impresso.
- **Codex CLI/TUI**: `/rename` para a thread atual.
- **Antigravity CLI**: `/rename <titulo>`.

## O que NAO fazer

Editar arquivos internos de historico (`~/.codex`, `~/.claude`, etc.) nao e o caminho. Esses formatos sao privados, podem mudar e podem nao atualizar a UI ativa.
