# ADR-0019: VERSION (raiz) e a fonte unica do numero de versao

- **Status:** Aceita
- **Data:** 2026-06-23

## Contexto

O numero de versao do pack vivia em **tres lugares** sem sincronia automatica:

- `VERSION` (raiz) — `0.4.0`, mas **nao era lido por nenhum codigo nem CI** (verificado na auditoria D-094). Servia so como convencao de release.
- `plugins/guia/.claude-plugin/plugin.json` — campo `version`, mantido a mao.
- `.claude-plugin/marketplace.json` (raiz) — campo `version` do plugin, mantido a mao.

Tres copias do mesmo numero, atualizadas manualmente, e um convite ao drift: bastava esquecer uma no bump. A auditoria D-094 (limpeza da superficie da raiz) levantou o `VERSION` orfao como candidato a resolver — ou remover, ou tornar fonte de verdade. O dono escolheu **torna-lo a fonte unica**, com o build propagando o numero.

## Decisao

`VERSION` (raiz) e a **fonte unica** do numero de versao. O renderer
(`core/build/render-skills.py`) le o `VERSION` e propaga o numero para o campo
`version` de `plugin.json` e `marketplace.json`, preservando todo o resto desses
arquivos (name, description, metadados continuam mantidos a mao). `render --check`
acusa drift; a CI (`render-check`/`release`) ja roda `--check`, entao um bump que
esqueca de rodar o render quebra o build.

Bump de versao agora: editar `VERSION` e rodar `python core/build/render-skills.py`.

## Consequencias

- + Um lugar so pra bumpar a versao; o build elimina o drift das 3 copias.
- + `--check` (ja na CI) vira gate: JSON fora de sincronia com o VERSION falha o build.
- + Preserva os JSONs byte-a-byte fora do campo `version` (sync cirurgico por regex, nao reserializa).
- - O `render-skills.py` ganha responsabilidade alem de skills (agora tambem versiona). Mitigado: secao isolada + ADR.
- - O sync exige exatamente 1 campo `"version"` semver por arquivo; muda esse layout e o sync aborta com erro explicito (intencional).

## Alternativas consideradas

- **Remover o `VERSION` e eleger `plugin.json` como fonte** (opcao A do D-094): −1 arquivo na raiz, zero build novo. Recusada: o dono prefere bumpar num arquivo dedicado e simples (`VERSION`) a editar JSON.
- **Reserializar os JSONs via `json.dumps`:** mais robusto que regex, mas reformata o arquivo inteiro (indentacao, ordem) e poluiria o diff. Recusada em favor do replace cirurgico do campo.

## Links

- Auditoria que levantou o item: `docs/auditorias/D-094-raiz-core-plugin.md` (P1).
- Implementacao: `core/build/render-skills.py` (`collect_version_outputs`), `tests/test_version_sync.py`.
- Relaciona: ADR-0006 (layout do plugin), ADR-0017 (core/src flat).
