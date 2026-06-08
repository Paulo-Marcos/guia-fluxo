# ADR-0005: Hook de docs bloqueante no `/finish`

- **Status:** Aceita
- **Data:** 2026-06-01

## Contexto

O pack tinha um vacuo entre "feature foi entregue" e "documentacao reflete a feature". O fluxo `ready -> humano valida -> finish` cobria estado da task, lock de arquivos e commit, mas nao tocava nos docs vivos do projeto (README, FEATURES.md, CHANGELOG, docs/reference, docs/explanation, ADRs). Resultado pratico: docs apodreciam por puro esquecimento, mesmo com agente disciplinado.

A boa pratica conhecida (Diataxis, ja em uso) descreve **onde** colocar cada tipo de doc, mas nao **quando** disparar a atualizacao. Faltava o gate.

## Decisao

Adicionar um hook de docs ao `guia.py finish` que:

1. Le `.guia/docs-map.yaml` (declaracao curada do humano: quais docs sao vivos e quando devem ser considerados);
2. Computa candidatos a partir dos triggers (`task-finished`, `touched`, `architectural-decision`);
3. Bloqueia o fechamento ate o agente registrar `--docs-touched <path>` (atualizou) e/ou `--docs-skip "<motivo>"` (avaliou e nao precisava);
4. Grava o resultado em `task.docsReview` para auditoria futura;
5. Vira no-op com aviso amigavel quando o projeto nao tem mapa (continua portavel para projetos que nao adotam controle de docs).

Tambem foi exposto `guia.py docs-check [task]` como subcomando standalone (texto ou `--json`) para o agente poder consultar a qualquer momento, nao so no fim.

## Consequencias

- + Cria pressao positiva pra docs ficarem vivos: o agente precisa **decidir** sobre cada candidato a cada `finish`.
- + Repete a decisao do humano (mapa em YAML) em vez de depender de memoria do agente.
- + O proprio pack dogfooda: este repo tem `.guia/docs-map.yaml` listando seus 9 docs vivos.
- + Mantem portabilidade: projeto sem mapa nao paga custo nenhum.
- - Aumenta a area de manutencao: doc novo so vira "vivo" se entrar no mapa.
- - Curva de aprendizado nova para o humano (campos do YAML, novas flags do finish).
- - Bloqueio do `finish` adiciona atrito real em demandas pequenas. Mitigacao: `--docs-skip` aceita motivo livre curto.

## Alternativas consideradas

- **Checklist em CONTRIBUTING/CLAUDE.md.** Solucao "soft". Foi o estado anterior - falhou pelo motivo classico: instrucao sem enforcement vira ruido.
- **Hook so na skill `/finish` (sem mudanca no CLI).** Skill desvia facilmente. Como `finish` ja e o gate de fechamento, faz sentido o enforcement viver no CLI - skill ensina, CLI obriga.
- **Geracao automatica de entrada de changelog/diff.** Mistura "abrir o palco" com "preencher conteudo". Esta ADR fica em "abrir o palco". Geracao automatica pode virar feature futura sem reabrir esta decisao.

## Links

- Explicacao: [`docs/explanation/por-que-docs-hook.md`](../explanation/por-que-docs-hook.md)
- How-to: [`docs/how-to/manter-docs-atualizados.md`](../how-to/manter-docs-atualizados.md)
- Reference: [`docs/reference/docs-map.md`](../reference/docs-map.md)
- Feature: F-010
