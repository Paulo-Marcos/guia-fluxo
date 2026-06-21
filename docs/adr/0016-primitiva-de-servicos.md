# ADR-0016: Camada de serviços (`guia service`) — considerada e RECUSADA

- **Status:** Recusada
- **Data:** 2026-06-20 (proposta) → 2026-06-21 (recusada)

## Contexto

O backlog tinha cinco demandas com a mesma forma: apontar um alvo, acionar um conjunto configurado de skills com um critério, produzir um resultado.

- **D-066** — registro de skills do projeto por tema.
- **D-065** — auditoria de pasta/feature com nota.
- **D-064** — avaliação tema vs projeto.
- **D-062** — avaliar arquitetura (DDD/SOLID) ao criar lock.
- **D-063** — commits funcionais por feature.

A proposta inicial (aceita por um turno, nunca commitada) era criar um **terceiro domínio**, Serviços: um catálogo `.guia/services.yaml` (serviço = receita de orquestração: quais skills, prompt, saída), CRUD determinístico `guia service add/edit/remove/list/show/run` espelhando os locks, e execução agent-driven via `/guia:service`. O dono reabriu a decisão questionando a vantagem real frente a "só usar skills + um plugin próprio".

## Decisão

**Não criar a camada/domínio de serviços.** As rotinas de qualidade viram **skills** (Agent Skills / `SKILL.md`), agrupadas num **plugin próprio do usuário** quando fizer sentido. O Guia Fluxo permanece com **dois** domínios: Demandas e Locks.

## Por que recusada

A pergunta-chave — *o que um `guia service` faz que uma skill não faz?* — não tem resposta convincente:

- **Skill já faz tudo:** recebe alvo, carrega critério no corpo, **orquestra outras skills**, produz saída estruturada. As 5 demandas já são, no fundo, skills.
- **Catálogo/CRUD reinventa o que já existe:** um plugin com as skills do usuário (ou `.claude/skills/`) **é** a personalização. O `services.yaml` duplica isso.
- **Cross-tool já coberto:** `SKILL.md` (Agent Skills) é lido nativamente por Codex e Antigravity. Escreve-se uma vez, três hosts leem — sem camada de serviço.
- **A analogia com locks não vale:** locks precisam de registry+CLI porque são aplicados por hook no commit e editar à mão é arriscado. Serviços não têm enforcement; editar um `SKILL.md` à mão é seguro. Logo o CRUD inteiro era overhead.
- **`manifest→render` é bazuca para mosca:** ele existe porque os *verbos* do guia precisam de invocação host-específica (chamar a CLI de jeitos diferentes). Uma skill consultiva ("audite esta pasta") é só instrução — não precisa disso.

Conclusão: a camada seria uma **indireção de registry** sobre skills, sem ganho funcional.

## Consequências

- + **Menos superfície:** zero domínio novo (sem `_services.py`, schema, runner, docs).
- + **Mecanismos nativos:** plugins e `SKILL.md` — composáveis, distribuíveis, cross-tool.
- + **Personalização real:** o plugin do usuário é a cara dele, sem máquina extra no guia.
- − Skills do usuário **não** nascem do `manifest→render` do guia. Se um dia quiser dual-render cross-tool sincronizado a partir de uma fonte, isso é uma **feature pequena futura** ("permitir skills custom no render"), não esta camada.
- − Sem um "registry central" de rotinas — mitigado: o próprio host/plugin já lista as skills disponíveis.

## Disposição das demandas

- **D-063 / D-064 / D-065** → viram **skills** (no plugin do usuário); saem do core do Guia Fluxo.
- **D-062** (arquitetura ao criar lock) → continua sendo uma **possível feature do guia** (uma skill/hook disparada no lock), **independente** desta camada. Re-abrir como item simples se priorizada.
- **D-066** (skills por tema) → **desnecessário**: uma única skill orquestradora cobre o agrupamento.
- **D-084** (implementação Fase 1 dos serviços) → **cancelada**.
- **Reativadas (2026-06-21)** para não se perderem, com IDs novos no backlog ativo: **D-085** (valida-pasta ← D-065), **D-086** (avalia-tema ← D-064), **D-087** (commits-funcionais ← D-063), **D-088** (arquitetura no lock ← D-062, feature do guia), **D-089** (skill orquestradora por tema ← D-066). Os IDs antigos seguem `Resolvida` (registro histórico).

> Débito honesto: os 5 (D-062..066) foram marcados `Resolvida` *antes* desta recusa, com razão "absorvido pela primitiva" — imprecisa agora. A CLI não tem `unresolve`, então a razão ficou no histórico; **este ADR é o registro canônico** da disposição correta. Cruza com a lição do D-081 (resolver/finalizar antes da decisão final deixa estado difícil de corrigir).

## Alternativas consideradas

- **Camada de serviço com CRUD (proposta original).** Recusada — ver acima.
- **`themes:` no `manifest.yaml` (build-time).** Catálogo seria do mantenedor do pack, não do consumidor; não personaliza.
- **Skills + plugin próprio (ESCOLHIDA).** Nativo, cross-tool via `SKILL.md`, sem domínio novo.

## Links

- Demandas: D-062, D-063, D-064, D-065, D-066 (parqueadas), D-084 (cancelada).
- Domínio de Locks (a analogia que não se sustentou): ADR-0002, `core/src/_locks.py`.
- Pipeline cross-tool: ADR-0008, ADR-0012/0013.
