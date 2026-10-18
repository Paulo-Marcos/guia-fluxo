# Como renomear o chat (opcional)

Todo comando do CLI (`feature`, `bug`, `chore`, `ready`, `finish`, `status`) imprime o titulo da **demanda corrente** no formato:

```text
NOME DA DEMANDA: D-016 ✨ - #DEV - Titulo
NOME DA DEMANDA: D-016 ✨ - #VALIDACAO - Titulo
NOME DA DEMANDA: D-016 ✨ - #FINALIZADO - Titulo
```

A mesma linha e o **nome do chat** da demanda ([ADR-0020](../adr/0020-chat-nomeado-pela-demanda-um-chat-por-demanda.md)): cada demanda tem o seu chat, e o titulo acompanha a etapa.

## Regra operacional

1. Depois de qualquer comando, o agente **repete no chat** a linha `NOME DA DEMANDA: ...`.
2. No Claude Code desktop, o agente **renomeia a sessao** para essa linha exata com `mcp__ccd_session_mgmt__set_session_title` (`session_id: "self"`). A tool fica adiada: o agente carrega com ToolSearch `select:mcp__ccd_session_mgmt__set_session_title`. Se voce mesmo deu o titulo a mao, o app pede sua aprovacao antes de trocar.
3. Demanda nova que aparece no meio de outra vira **outro chat**, relacionado a este, aberto pelo agente com `start_session` ja no padrao do Guia (`D-NNN <emoji> - #PLANEJADA - Titulo`) e no **modelo recomendado** pelo `triage`. O chat novo comeca com `start D-NNN` e se renomeia para `#DEV`.
4. O agente grava o nome estavel com `chat D-NNN --title "..."` - e o nome que a fila cita em "volte ao chat". Busque o `D-NNN` na barra lateral.

## Sem a tool de rename

Fora do Claude Code desktop, ou numa sessao desatendida:

- **Claude Code CLI**: `mark_chapter` (divisor + entrada na ToC, feito pelo agente) e `/rename <titulo>` digitado por voce, ou `claude -n <titulo>` ao abrir. O launcher `gf` cria a demanda e abre a sessao nomeada - ver [criar-demanda-pelo-terminal.md](criar-demanda-pelo-terminal.md). O helper `core/bin/guia-rename.ps1` / `core/bin/guia-rename` copia o titulo de `.guia/demand-title.txt` para o clipboard.
- **Codex App**: `codex_app.set_thread_title` com o titulo impresso.
- **Codex CLI/TUI** e **Antigravity CLI**: `/rename <titulo>`.

Lista completa em [reference/chat-rename-suporte.md](../reference/chat-rename-suporte.md).

## O que NAO fazer

Editar arquivos internos de historico (`~/.codex`, `~/.claude`, etc.) nao e o caminho. Esses formatos sao privados, podem mudar e podem nao atualizar a UI ativa.
