# Como renomear o chat (opcional)

Todo comando do CLI (`feature`, `bug`, `chore`, `ready`, `finish`, `status`) imprime o titulo da **demanda corrente** no formato:

```text
NOME DA DEMANDA: D-016 ✨ - #DEV - Titulo
NOME DA DEMANDA: D-016 ✨ - #VALIDACAO - Titulo
NOME DA DEMANDA: D-016 ✨ - #FINALIZADO - Titulo
```

Isso e **informacao da demanda**, nao um titulo de chat. O print **nao** renomeia a UI, e um mesmo chat pode conter varias demandas (um epico `E-001` com suas stories — ver [ADR-0018](../adr/0018-nome-da-demanda-chat-diferente-de-demanda.md)). Renomear o chat e uma conveniencia **opcional** do usuario.

## Regra operacional

Depois de qualquer um desses comandos, o agente **repete no chat** a linha `NOME DA DEMANDA: ...` — e o sinal de rastreabilidade entre o trabalho e a demanda.

## Renomear o chat na UI (quando ajudar)

So vale a pena quando **uma** demanda mapeia limpo para o chat. Se o chat ja agrega varias demandas, renomear para o titulo de uma so engana — nesse caso, nao renomeie.

A forma muda por ferramenta. Ver [reference/chat-rename-suporte.md](../reference/chat-rename-suporte.md) para a lista completa.

Resumo rapido:

- **Claude Code**: `mark_chapter` (divisor + entrada na ToC, feito pelo agente) e/ou `/rename <titulo>` durante a sessao (digitado por voce), ou iniciar com `claude -n <titulo>`. Para ja criar a demanda **e** abrir a sessao nomeada de uma vez pelo terminal, use o launcher `gf` — ver [criar-demanda-pelo-terminal.md](criar-demanda-pelo-terminal.md). Para uma sessao **ja aberta** nao ha rename por fora: o helper `core/bin/guia-rename.ps1` / `core/bin/guia-rename` le `.guia/demand-title.txt`, copia o titulo para o clipboard e o imprime — voce so da `/rename` + cola.
- **Codex App**: `codex_app.set_thread_title` com o titulo impresso.
- **Codex CLI/TUI**: `/rename` para a thread atual.
- **Antigravity CLI**: `/rename <titulo>`.

## O que NAO fazer

Editar arquivos internos de historico (`~/.codex`, `~/.claude`, etc.) nao e o caminho. Esses formatos sao privados, podem mudar e podem nao atualizar a UI ativa.
