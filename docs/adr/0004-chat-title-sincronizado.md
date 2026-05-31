# ADR-0004: Chat-title sincronizado com a task corrente

- **Status:** Aceita
- **Data:** 2026-05-31

## Contexto

Quem usa varios chats de IA em paralelo perde rapidamente qual chat era sobre o que. Sintomas:

- Voce abre um chat para mexer em `F-006`, sai para responder Slack, volta 30 minutos depois sem saber se aquele chat era do `F-006` ou do `I-003`.
- Agentes diferentes (Codex, Claude, Antigravity) tem APIs distintas (ou nenhuma) para renomear a sessao.
- Sem convencao, cada agente nomeia chat de um jeito; histograma de nomes vira lixo.

Solucao precisa funcionar **independente da API do agente** (alguns nao expoem `rename_chat`) e **convergir** para o mesmo titulo nao importa qual ferramenta esta sendo usada.

## Decisao

Toda operacao do script que muda a task corrente (`feature`, `issue`, `ready`, `finish`, `promote`) imprime no stdout uma linha:

```
NOME DO CHAT: F-016 - #DEV - Titulo curto da task
```

e grava o mesmo titulo em `.ai/chat-title.txt`. Convencoes:

- Prefixo do ID (`F-016`, `I-003`).
- Tag de fase (`#DEV` em desenvolvimento, `#VAL` em validacao, `#FINALIZADO` validado/lockado).
- Titulo da task.

O agente repete essa linha no chat (visivel ao humano) e tenta aplicar via API/comando da ferramenta **quando disponivel**. Quando nao disponivel, a linha repetida ja resolve para o humano.

## Consequencias

- + Funciona em **qualquer agente**, com ou sem API de rename. Degrada graciosamente.
- + Convergencia: troca de ferramenta no meio da task nao perde o titulo - `.ai/chat-title.txt` carrega a verdade.
- + Sinal visual no chat: cada vez que voce roda `/status` ou `/ready`, o nome reaparece no historico, reforcando contexto.
- + Tag de fase muda automaticamente: `#DEV` -> `#VAL` -> `#FINALIZADO` sinaliza progresso sem precisar abrir nada.
- - Convencao **convivencial**: depende do agente honrar o protocolo. Mitigado pela skill, que treina o agente.
- - Linha extra no stdout polui scripts terceiros que parseiam saida do `ai.py` (resolvido: a linha tem prefixo estavel `NOME DO CHAT:` e pode ser filtrada).
- - Ferramentas sem API de rename: humano ainda tem que renomear manualmente se quiser (mas a sugestao esta a um copy-paste de distancia).

## Alternativas consideradas

- **API-only:** rejeitada porque Codex CLI e algumas integracoes Antigravity nao expoem rename. Quebraria paridade entre agentes.
- **So gravar em arquivo, sem stdout:** o sinal visual no chat seria perdido. O reforco visual e parte do valor.
- **Nome fixo baseado em branch:** acopla a estrategia git e nao reflete fase da task.

## Links

- Reference por ferramenta: [`../reference/chat-rename-suporte.md`](../reference/chat-rename-suporte.md).
- How-to: [`../how-to/renomear-chat.md`](../how-to/renomear-chat.md).
- [ADR-0001](0001-script-fonte-da-verdade.md) - o script sempre imprime e grava, garantindo a unica fonte.
