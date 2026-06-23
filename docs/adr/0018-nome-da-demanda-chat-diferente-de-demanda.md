# ADR-0018: `NOME DA DEMANDA` — o chat nao e a demanda

- **Status:** Aceita
- **Data:** 2026-06-23
- **Substitui:** [ADR-0004](0004-chat-title-sincronizado.md)

## Contexto

A [ADR-0004](0004-chat-title-sincronizado.md) decidiu que todo verbo imprimiria `NOME DO CHAT: <ID> - #<fase> - <titulo>` e gravaria o mesmo titulo em `.guia/chat-title.txt`, partindo do pressuposto **1 chat = 1 task**. Duas coisas furaram esse pressuposto:

1. **O print nunca renomeou o chat de verdade.** Em Claude Code o chat so muda por `/rename` manual ou `mark_chapter`; em Codex/Antigravity depende de API que nem sempre existe. Ou seja, `NOME DO CHAT:` anunciava uma renomeacao que, na pratica, nao acontecia — o sistema *mentia* sobre o que estava fazendo.
2. **O epico (D-049) quebrou o 1:1.** Um chat-pai passou a conter **varias** demandas/stories (`E-001` + `D-100`, `D-101`...). Chamar a linha de "nome do chat" virou contradicao: qual das demandas seria o nome do chat?

Conclusao: o que o script tem para oferecer e **informacao da demanda corrente**, nao um titulo de chat. Renomear o chat e uma escolha do usuario, nao um efeito do comando.

## Decisao

1. **Trocar o rotulo.** O script passa a imprimir:

   ```
   NOME DA DEMANDA: D-093 ✨ - #DEV - Titulo curto da demanda
   DEMAND_TITLE=D-093 ✨ - #DEV - Titulo curto da demanda
   ```

   E informacao pura da demanda corrente. **Nao** afirma renomear o chat.

2. **Renomeacao do chat vira OPCIONAL.** As skills passam a tratar `mark_chapter`/`/rename` (Claude) e `codex_app.set_thread_title` (Codex) como conveniencia, aplicada so quando uma demanda mapeia limpo para o chat e ajuda navegacao — nunca como passo obrigatorio, e explicitamente pulada quando o chat tem varias demandas.

3. **Renomeacoes internas (consistencia do modelo chat ≠ demanda):**
   - `print_chat_title` -> `print_demand_title`.
   - `chat_title()` -> `demand_title()`.
   - Chave do payload em `.guia/current-task.json`: `chatTitle` -> `demandTitle`.
   - Config em `process.json`: `chatTitleFormat` -> `demandTitleFormat` (com **fallback de leitura** para a chave legada `chatTitleFormat`, para projetos ja inicializados antes desta mudanca).
   - Constantes: `CHAT_TITLE_FORMAT_DEFAULT` -> `DEMAND_TITLE_FORMAT_DEFAULT`; `CHAT_TITLE_FILE` -> `DEMAND_TITLE_FILE`.

4. **Manter o arquivo, renomeado: `.guia/chat-title.txt` -> `.guia/demand-title.txt`.** Continua sendo um pointer estavel e host-agnostico para o titulo da demanda corrente, que um helper externo de rename pode ler — agora com o nome certo. Permanece gitignorado (volatil). Nenhum consumidor faz parsing de `NOME DO CHAT:`/`CHAT_TITLE=` no stdout (auditado antes da renomeacao), entao trocar os rotulos e seguro.

## Consequencias

- + O sistema para de mentir: o que ele imprime e o que ele entrega (info da demanda), sem fingir renomear nada.
- + Coerente com o epico: um chat com varias demandas nao tem mais um "nome do chat" forcado; cada comando reporta a demanda que tocou.
- + Renomear continua possivel para quem quer — degradacao graciosa preservada da ADR-0004, agora como opt-in consciente.
- - Mudanca de rotulo no stdout (`NOME DO CHAT:` -> `NOME DA DEMANDA:`, `CHAT_TITLE=` -> `DEMAND_TITLE=`). Mitigado: nenhum parser conhecido depende dos rotulos antigos; a busca no repo nao achou consumidor de stdout.
- - `process.json` de projetos antigos ainda traz `chatTitleFormat`. Mitigado pelo fallback de leitura (`demandTitleFormat` || `chatTitleFormat` || default); novos `init` ja gravam `demandTitleFormat`.
- - O arquivo `.guia/chat-title.txt` antigo pode sobrar local (gitignorado, inofensivo) ate ser apagado a mao.

## Alternativas consideradas

- **Apagar o arquivo `demand-title.txt` de vez:** o `current-task.json` ja carrega `demandTitle`, entao o txt e redundante. Recusada por ora — manter um pointer de 1 linha, trivialmente `cat`-avel, custa quase nada e preserva o beneficio de convergencia entre ferramentas que a ADR-0004 citava.
- **Manter `NOME DO CHAT` e so documentar que e opcional:** recusada — o rotulo continuaria afirmando algo falso. O problema raiz e semantico, nao de documentacao.
- **Renomear `process.json` sem fallback:** quebraria o titulo de projetos ja inicializados. Recusada em favor do fallback de leitura.

## Links

- Reference por ferramenta: [`../reference/chat-rename-suporte.md`](../reference/chat-rename-suporte.md).
- How-to: [`../how-to/renomear-chat.md`](../how-to/renomear-chat.md).
- [ADR-0004](0004-chat-title-sincronizado.md) — decisao original, agora substituida.
- [ADR-0011](0011-modelo-de-demanda-tipo-x-status.md) e o epico D-049 — o que quebrou o pressuposto 1 chat = 1 task.
