# Architecture Decision Records (ADRs)

Registros curtos das decisoes arquiteturais que moldaram o pack. Cada ADR responde tres perguntas: **qual era o contexto**, **o que foi decidido** e **quais as consequencias**.

Por que existem: em 6 meses, voce ou outro contribuidor esquece por que algo foi feito do jeito que esta. Sem ADR, alguem abre o repo, ve a decisao como "estranha", refaz e quebra um caso ja resolvido. ADR e vacina contra esse retrabalho.

ADR nao se confunde com [`explanation/`](../explanation/): explanation ensina o conceito (pedagogico, pode ser longo); ADR e o registro factual da decisao (Contexto / Decisao / Consequencias). Quando os dois cobrem o mesmo tema, o ADR e a fonte canonica e a explanation linka para ele.

## Indice

| ADR | Decisao | Status |
| --- | --- | --- |
| [0001](0001-script-fonte-da-verdade.md) | Script Python e a fonte de verdade, nao o agente | Aceita |
| [0002](0002-lock-por-commit-message.md) | Unlock por marca no commit-message, nao arquivo separado | Aceita |
| [0003](0003-json-maquina-markdown-humano.md) | JSON para maquina, Markdown para humano | Aceita |
| [0004](0004-chat-title-sincronizado.md) | Chat-title sincronizado com a task corrente | Aceita |

## Como adicionar um ADR novo

1. Copie [`template.md`](template.md) para `NNNN-titulo-em-kebab.md` com o proximo numero sequencial.
2. Preencha Contexto, Decisao, Consequencias. Mantenha curto (1-2 paginas).
3. Inclua o ADR no indice acima.
4. Status inicial e **Proposta**. Vira **Aceita** quando voce mergea a decisao.
5. Se uma decisao posterior derrubar este ADR, marque **Substituida por ADR-NNNN** em vez de apagar - o historico importa.

## Convencoes

- Numeracao monotonica crescente, comecando em 0001. Nunca reaproveite numero.
- Nome do arquivo em kebab-case, descritivo: `0007-cache-em-memoria.md`.
- Status possiveis: **Proposta**, **Aceita**, **Substituida**, **Depreciada**.
- Datas em ISO (YYYY-MM-DD).
- Linguagem objetiva. Sem prosa motivacional - quem chega aqui ja sabe que precisa entender uma decisao especifica.
