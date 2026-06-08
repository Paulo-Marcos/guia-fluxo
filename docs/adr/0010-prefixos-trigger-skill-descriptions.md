# ADR-0010: Prefixos de marcador nas descriptions das skills

- **Status:** Aceita
- **Data:** 2026-06-03

## Contexto

A F-003 introduziu marcadores em CAPS no inicio de cada description do
manifest para evitar trigger collision entre as skills do pack
(`feature`, `issue`, `backlog`, `promote`, `ready`, `finish`, `status`,
`guia-fluxo`). Cada prefixo sinaliza ao roteador do agente (Claude
Code, Codex, Antigravity) quando NAO disparar a skill.

A auditoria [`F-014`](../auditorias/F-014-core.md) na Etapa 1 achado 6
notou: **a politica de prefixos so vive na PR de F-003 e no commit log**.
Proximo editor de uma description nao tem onde consultar a convencao,
podendo quebrar o sistema sem perceber.

Vocabulario atual em uso (verificado via `grep`):

- `PRIMARY TRIGGER for /<verbo>` — verbo cria task imediatamente.
- `DEFER-AND-PARK` — guarda ideia futura sem comecar implementacao.
- `EVALUATE-AND-CONVERT` — avalia um backlog item especifico antes de
  promover.
- `HANDOFF to developer validation` — entrega para validacao manual sem
  fechar.
- `CLOSE an ALREADY-validated task` — fecha task ja validada.
- `READ-ONLY` — so inspeciona, nao muda estado.
- `REFERENCE/BACKGROUND ONLY` — carrega contexto, nao e gatilho direto.

E cada description termina com `Do NOT use for: ... (use $<outro-verbo>)`
listando quando rejeitar o trigger e qual skill irma usar.

## Decisao

Documentar a politica de prefixos como invariante do manifest. Ao
editar `verbs.<verbo>.description`:

1. Comecar com um dos **7 prefixos canonicos** (listados na tabela
   abaixo) escolhidos por intencao primaria da skill.
2. Manter o restante da description em ate ~3-4 linhas explicando o
   gatilho ("Triggered by ...").
3. Encerrar com `Do NOT use for: <caso> (use $<outro-verbo>)` cobrindo
   os 2-3 verbos vizinhos que poderiam ser confundidos com este.

Renderer (`core/build/render-skills.py`) continua aceitando qualquer
texto - a invariante e **convencao social** entre editores, nao validacao
mecanica. Auditoria periodica pelo dev confirma aderencia.

### Tabela de prefixos canonicos

| Prefixo | Quando usar | Skills atuais |
|---|---|---|
| `PRIMARY TRIGGER for /<verbo>` | Verbo cria/avanca task imediatamente | `feature`, `bug`, `chore` |
| `DEFER-AND-PARK skill` | Guarda futuro sem comecar implementacao | `backlog` |
| `EVALUATE-AND-CONVERT one specific backlog item` | Avalia 1 backlog item especifico | `promote` |
| `HANDOFF to developer validation` | Entrega para validacao sem fechar | `ready` |
| `CLOSE an ALREADY-validated task` | Fecha task ja validada | `finish` |
| `READ-ONLY` | Inspeciona, nao muda estado | `status` |
| `REFERENCE/BACKGROUND ONLY` | Carrega contexto, nao e gatilho direto | `guia-fluxo` |
| `TERMINAL CANCEL` | Encerra task como `Cancelada` (terminal) | `cancel` |
| `PAUSE in-flight task` | Pausa preservando WIP (status `Bloqueada`) | `block` |
| `RESUME a paused task` | Sai de `Bloqueada` para `Em desenvolvimento` | `unblock` |
| `PLAN` | Marca como `Planejada` (triada mas nao iniciada) | `plan` |
| `START` | Comeca trabalho (Backlog/Planejada -> `Em desenvolvimento`) | `start` |

### Addendum (F-027, F-029, D-039, D-042)

5 prefixos novos foram adicionados acima depois do ADR original:
- `TERMINAL CANCEL` em F-027 ([cancel](../../core/manifest/manifest.yaml)).
- `PAUSE in-flight task` + `RESUME a paused task` em F-029 ([block/unblock](../../core/manifest/manifest.yaml)).
- `PLAN` + `START` em D-039 ([plan/start](../../core/manifest/manifest.yaml)), parte da Fase 3 do ADR-0011 e tambem entrega B-017.

Mudanca tambem em D-042 (Fase 4 do ADR-0011): a skill `issue` foi
removida; o prefixo `PRIMARY TRIGGER for /<verbo>` agora cobre
`feature`, `bug` (novo) e `chore` (novo) em vez de `feature`+`issue`.

Politica continua a mesma: descricoes comecam com um destes 12 prefixos,
explicam o gatilho em 2-4 linhas e terminam com `Do NOT use for: ...`
listando vizinhos confundiveis. Renderer continua sem validacao
mecanica; convencao social entre editores.

## Consequencias

- + Proximo editor de uma description tem 1 doc que documenta as 7
  classes de skill + a clausula `Do NOT use for`.
- + Skill nova entra escolhendo um prefixo: se nenhum encaixa, e sinal
  de que a skill duplica outra existente (alarme antes de criar
  conflict de trigger).
- + Auditoria fica facil: `grep` pelo prefixo em `manifest.yaml` mostra
  a distribuicao real e revela skill sem prefixo.
- - Politica e social, nao mecanica. Renderer nao valida. Editor pode
  ignorar - mitigado por `--check` futuro (achado 1.7 do audit) que
  pode rodar regex contra esta tabela.
- - Sete classes podem nao cobrir todos os casos de skill futura. Se um
  caso novo aparecer, ele propoe um 8o prefixo via ADR addendum.

## Alternativas consideradas

- **Sem politica explicita (status quo pre-ADR)**: rejeitada porque ja
  causou retrabalho silencioso (F-003 nasceu para corrigir colisao).
- **Validacao mecanica no renderer**: rejeitada por enquanto - vira
  pratico quando o pack expandir para >10 verbos, hoje o overhead nao
  compensa.
- **JSON-Schema no description com `pattern`**: rejeitada por
  acoplamento alto ao YAML schema (que ja e instavel).

## Links

- [Auditoria F-014, Etapa 1 achado 6](../auditorias/F-014-core.md)
- [F-003 na FEATURES.md](../../FEATURES.md) - origem da politica.
- [ADR-0008](0008-layout-b-manifest.md) - decisao de manter
  descriptions inline (separadas dos bodies). Reforca este ADR.
- [`core/manifest/manifest.yaml`](../../core/manifest/manifest.yaml) -
  fonte unica das descriptions.
