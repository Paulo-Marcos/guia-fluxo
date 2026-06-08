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
| [0005](0005-docs-hook-no-finish.md) | Hook de docs bloqueante no `/finish` | Aceita |
| [0006](0006-plugin-oficial-claude-code.md) | Adotar layout oficial de plugin Claude Code com namespace `ai` | Aceita |
| [0007](0007-arquitetura-modular-core-src.md) | Decompor `core/src/guia.py` em modulos com Clean Architecture | Aceita |
| [0008](0008-layout-b-manifest.md) | Manifest em layout B (index YAML + bodies markdown) | Aceita |
| [0009](0009-yaml-para-manifest.md) | YAML como formato do manifest (decisao retroativa documentada) | Aceita |
| [0010](0010-prefixos-trigger-skill-descriptions.md) | Politica de prefixos canonicos nas descriptions das skills | Aceita |
| [0011](0011-modelo-de-demanda-tipo-x-status.md) | Modelo de demanda: `kind` x `status` ortogonais, backlog vira status, ID neutro `D-NNN` | Aceita |

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
