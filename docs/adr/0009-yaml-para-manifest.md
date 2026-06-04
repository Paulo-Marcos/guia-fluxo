# ADR-0009: YAML como formato do manifest de skills

- **Status:** Aceita
- **Data:** 2026-06-03

## Contexto

`core/manifest/manifest.yaml` (index das skills + descriptions; ADR-0008
moveu os bodies para markdown) sempre foi YAML, mas a decisao nunca foi
documentada. A auditoria [`F-014`](../auditorias/F-014-core.md) na Etapa
1 Q1 levantou o ponto: o ADR-0003 explicitamente rejeita YAML como
fonte de estado de tasks ("whitespace-sensitive, diff ruidoso em
arrays"), porem aquele contexto eram dados de processo (`.ai/*.json`).
O manifest e outra coisa - geracao de skill files em build-time.

Restricoes/forces no momento da decisao tacita:

- Descriptions (`description: |`) sao strings multi-linha curtas (3-10
  linhas) com pontuacao e marcadores estilo "PRIMARY TRIGGER ... Do NOT
  use for...". JSON exigiria escape `\n` em toda linha (inviavel para
  edicao humana).
- O renderer ja precisa de PyYAML (idem `check-lock.py` para registry,
  `core/src/_docs_hook.py` para `docs-map.yaml`). Sem custo de
  dependencia adicional.
- O frontmatter dos `SKILL.md` gerados ja e YAML (padrao Anthropic/Claude
  Code). Manter o mesmo formato no source reduz mismatch mental.

Dores reais com YAML observadas:

- **Whitespace-sensitive**: indentacao errada quebra estrutura sem erro
  obvio. Mitigada por `--check` no CI (`render-skills.py --check`).
- **YAML 1.1: `on:` -> `True`**. **Ja virou bug**: ha workaround
  defensivo em `_docs_hook._trigger_reason` que recusa `trigger['on']`
  quando vira boolean. O caso e raro mas vale documentar.
- **Sem schema formal**: `yaml.safe_load + dict.get` em runtime; erros
  tardios. Mitigado em parte pelo `render-skills.py` que aborta em chaves
  esperadas ausentes (description vazio, target invalido, etc.).

Alternativas factuais consideradas:

| Formato | Multi-line | Schema | DX bodies markdown (pre-ADR-0008) | Custo migracao |
|---|---|---|---|---|
| **YAML (atual)** | `\|` block literal | Manual via PyYAML | Aceitavel | Zero |
| **JSON** | `\n` escapes | jsonschema | Inviavel | Alto |
| **TOML** | `"""` triplo | Manual | Verboso pra hierarquia | Medio |
| **N arquivos markdown + frontmatter** | Nativo | Frontmatter YAML | Otimo | Resolvido por ADR-0008 |

## Decisao

Manter YAML como formato do **index** do manifest. Bodies viraram
arquivos markdown puros via ADR-0008 (layout B), entao a parte
multi-linha problematica saiu. O que sobrou no YAML e estrutura curta
(`version`, `verbs.<verbo>.description`, `targets.<target>.body_file`)
onde os tradeoffs de YAML sao aceitaveis e a migracao para outro
formato traz custo sem ganho real.

## Consequencias

- + Zero custo de migracao (decisao retroativa do estado atual).
- + Frontmatter dos SKILL.md gerados continua coerente (YAML em YAML).
- + Mesma dependencia PyYAML ja exigida por outros componentes.
- + Bodies ja foram externalizados via ADR-0008, eliminando o pior caso
  de YAML (block literal extenso).
- - Whitespace-sensitive. Mitigado por `--check` + linter de pre-commit
  futuro (nao implementado).
- - Pegadinha YAML 1.1 `on:` continua valida em outros yaml files do
  projeto. Workaround documentado em `_docs_hook.py`.
- - Sem schema formal; erros de manifest viram traceback. Mitigado por
  `render-skills.py` que aborta com mensagem amigavel para os erros
  estruturais conhecidos.

## Quando reconsiderar

- Se a estrutura do index crescer alem de ~150 linhas, considerar
  TOML (mais explicito em hierarquias) ou um schema YAML formal
  (`pydantic` / `dataclasses-json`).
- Se outro bug do estilo `on:->True` aparecer no manifest e o workaround
  ficar caro, considerar migrar para JSON + pre-processador que aceita
  bodies via path (efetivamente layout B em JSON).

## Alternativas consideradas

- **JSON**: descartado pelo custo de escape de strings multi-linha (era
  o caso pre-ADR-0008; com bodies externos seria viavel mas perde
  legibilidade do `description:` block literal).
- **TOML**: descartado por verbosidade em hierarquia (`[verbs.feature.targets.agent_skill]`).
- **N YAMLs (1 por verbo)**: descartado em ADR-0008 - perde vista
  panoramica das descriptions (que e onde trigger collision aparece).

## Links

- [Auditoria F-014, Etapa 1 Q1](../auditorias/F-014-core.md)
- [ADR-0003](0003-json-maquina-markdown-humano.md) - JSON para dados de
  processo (.ai/*); este ADR e seu complemento para fonte de geracao.
- [ADR-0008](0008-layout-b-manifest.md) - layout B (index + bodies
  markdown) que resolve o pior caso de YAML.
- Workaround `on:->True` em `core/src/_docs_hook.py:_trigger_reason`.
