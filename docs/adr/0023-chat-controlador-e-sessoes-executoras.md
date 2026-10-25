# ADR-0023: chat controlador e sessoes executoras

- **Status:** Aceita
- **Data:** 2026-10-23
- **Estende:** [ADR-0020](0020-chat-nomeado-pela-demanda-um-chat-por-demanda.md) (uma demanda, um chat)

## Contexto

Entre 2026-10-20 e 2026-10-23 (D-187, D-190 a D-198) o dono trabalhou num estilo que a ADR-0020 permitia mas nao descrevia: um **chat principal** recebeu os pedidos, separou-os em demandas e abriu uma **sessao por demanda** (`start_session`). Esse chat repassou unlocks e approves do dono, acompanhou a fila, mandou as sessoes rebasearem em conflito, rodou `finish` com autorizacao e renomeou os chats.

Funcionou, mas com uma lacuna: as follow-ups D-195, D-196 e D-197 foram abertas por sessoes executoras que nao gravaram `chat.session` na demanda nova. Sem a sessao, a reconciliacao da D-194 (`chat --pending`) nao as viu, e o dono-controlador renomeou os tres chats a mao. O motor tambem nao sabia quem conduzia cada demanda: `status` e o painel mostravam o chat, nao o papel nem o controlador.

## Decisao

1. **Dois papeis.** O **controlador** e o chat que recebe os pedidos do dono e conduz varias demandas; a **executora** e a sessao que faz uma demanda. A demanda guarda o papel do chat que a faz (`chat.role`: `executor` ou `controller`) e, para a executora, o `sessionId` do controlador (`chat.controller`). O controlador pode fazer ele mesmo uma demanda pequena ou de coordenacao (o epico, a release): ai `role: controller`, sem `controller`.
2. **O controlador:** diagnostica e separa o pedido em demandas pelo motor (`feature`/`bug`/`chore` + `triage`); abre uma executora por demanda (`start_session` com `model`/`effort` do triage, brief comecando por `start D-NNN`, worktree do Guia); acompanha a fila e destrava (conflito -> manda a executora rebasear, reauditar e `queue add`); renomeia os chats (`chat --pending`); com autorizacao do dono roda `finish` com docs-check e revisao de qualidade; abre a release.
3. **A executora:** faz `start` ate `ready` e `next` ate `stop`/`done`, no worktree da demanda, e reporta ao controlador. Pergunta ao controlador (uma pergunta curta) quando trava numa decisao do dono.
4. **Autorizacao so do dono, e com as palavras dele.** Nenhum dos dois concede nada por conta propria: unlock, approve, autonomy, configure, `queue run`/`pause`/`resume` e `finish` continuam do dono (D-098, `queue-control`). O controlador repassa uma autorizacao citando o que o dono disse, entre aspas; a executora so age sobre autorizacao citada assim. Nenhum dos dois faz merge do PR.
5. **Quem abre a sessao grava a sessao.** Logo depois do `start_session`, quem o chamou - controlador ou executora abrindo uma follow-up - grava na demanda o id devolvido: `chat D-NNN --title "<nome>" --session <id> --role executor --controller <controlador>`. A follow-up herda o controlador da demanda de origem (`chat <origem> --json`). Ao rodar `start`, a executora confirma o proprio registro com o `sessionId` de `get_session("self")` e o controlador ja gravado na demanda ou citado no brief; so sem os dois, pelo `parentSessionId` (na follow-up proposta por uma executora, o pai e a executora, nao o controlador).
6. **O motor mostra e cobra.** `status` e o painel mostram papel e controlador ao lado do chat. `chat --pending` lista, alem dos nomes atrasados, as demandas abertas (DEV, validacao, PR, fila) sem sessao gravada (`AVISO CHAT: ...`), para o controlador ver a follow-up que ninguem registrou.

## Consequencias

- + O papel de cada chat fica escrito, e as autorizacoes do dono nao se diluem no repasse.
- + Follow-up aberta por executora entra na reconciliacao de nomes, sem rename manual.
- + `status`/painel dizem quem conduz a demanda, e o dono sabe a que chat voltar.
- - Mais um passo depois de cada `start_session`. Mitigado: o `AVISO CHAT` de `chat --pending`, `next` e `status` aponta o que faltou.
- - O controlador depende do app de sessoes relacionadas; sem ele (CLI, outro host) o estilo degrada para um chat por demanda aberto pelo dono, como na ADR-0020.

## Links

- [ADR-0020](0020-chat-nomeado-pela-demanda-um-chat-por-demanda.md)
- [how-to/renomear-chat.md](../how-to/renomear-chat.md)
