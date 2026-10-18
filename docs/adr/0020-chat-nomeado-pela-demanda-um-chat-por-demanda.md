# ADR-0020: o chat leva o nome da demanda, e cada demanda tem o seu chat

- **Status:** Aceita
- **Data:** 2026-10-18
- **Substitui em parte:** [ADR-0018](0018-nome-da-demanda-chat-diferente-de-demanda.md) (itens 2 e o pressuposto "um chat com varias demandas")

## Contexto

A ADR-0018 separou demanda de chat por dois motivos: (1) nao havia como o agente renomear uma sessao Claude Code de verdade - so `mark_chapter` e o `/rename` digitado; (2) o epico (D-049) fazia um chat-pai conter varias demandas.

Os dois mudaram no Claude Code desktop:

1. **Existe rename real.** A tool `mcp__ccd_session_mgmt__set_session_title` (com `session_id: "self"`) renomeia a sessao na barra lateral. Fica adiada; carrega com ToolSearch `select:mcp__ccd_session_mgmt__set_session_title`. Verificado na D-185, renomeando a propria sessao da demanda.
2. **Existem sessoes relacionadas.** `mcp__ccd_session__start_session` abre uma sessao nova ligada a atual (o app mostra a relacao e avisa quando ela termina um turno). Uma demanda derivada nao precisa mais morar no chat de quem a descobriu.

## Decisao

1. **Uma demanda, um chat.** Demanda que surge durante outra (story de epico, follow-up, bug achado no caminho) e criada pelo CLI (`--status planned`, ou `--under E-NNN`) e vai para uma sessao propria via `start_session`: `title` = linha `NOME DA DEMANDA` no padrao do Guia (`D-NNN <emoji> - #<ETAPA> - <titulo>`, nasce `#PLANEJADA` e vira `#DEV` no `start` do chat novo), `context: "fresh"`, brief comecando por `start <D-NNN>`. `initiation` segue a origem: `offer` quando o dono pediu a demanda, `user_asked` quando mandou comecar, `own_initiative` quando o agente a encontrou. O chat do epico guarda so o epico.
2. **O chat da demanda nasce no modelo recomendado.** O `triage` roda antes de decidir onde a demanda corre; `triage --json` da `model` e `effort`, que vao direto nos parametros de mesmo nome do `start_session`. A demanda so fica no chat atual quando ele nao tem outra demanda **e** ja roda no modelo recomendado. Como o `start_session` so desce de modelo, recomendacao acima do chat atual (Opus a partir de Sonnet, sugestao Fable) e avisada ao dono, nunca assumida.
3. **O chat leva o nome da demanda e acompanha a etapa.** Sempre que um verbo imprime `NOME DA DEMANDA` no chat da demanda, o agente renomeia a sessao para essa linha exata. O titulo passa de `#DEV` a `#VALIDACAO`, `#PR`, `#FILA`... e a barra lateral vira um painel das demandas.
4. **Nome estavel continua gravado (D-157).** `chat <D-NNN> --title` guarda o nome sem etapa (`D-NNN ✨ Titulo`), que a fila e o `status --all` citam. O titulo vivo comeca pelo mesmo `D-NNN`, entao buscar o ID na barra lateral acha o chat.
5. **A fila renomeia o chat ao integrar (D-188).** O chat grava o proprio `sessionId` junto do nome (`chat D-NNN --session <id>`). Ao integrar, o `queue run` imprime `RENOMEIE O CHAT: <sessionId> -> <NOME DA DEMANDA>` com a etapa final, e o chat gerente da fila chama `set_session_title` com esse id. O executor fica mecanico e sem MCP; sessao que recusa o rename vira aviso ao dono.
6. **Degradacao.** Sem a tool (CLI, outro host, sessao desatendida que recusa o rename): `mark_chapter` + `/rename` manual, como na ADR-0018. Codex segue com `codex_app.set_thread_title`.

## Consequencias

- + O nome do chat diz a demanda e a etapa, sem passo manual.
- + Cada demanda roda no modelo que o triage pediu, sem o dono trocar a mao.
- + Cada demanda tem historico proprio; o chat de origem nao vira um saco de demandas.
- - Mais sessoes abertas. Mitigado: sao relacionadas a de origem e podem ser arquivadas no fim.
- - O titulo vivo e o nome gravado diferem (etapa). Mitigado pelo prefixo `D-NNN` comum.
- - O rename pede aprovacao quando o dono deu o titulo a mao; o agente aceita a recusa e segue.

## Links

- [how-to/renomear-chat.md](../how-to/renomear-chat.md)
- [reference/chat-rename-suporte.md](../reference/chat-rename-suporte.md)
