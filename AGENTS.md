# AGENTS.md

Briefing para agentes de IA (Codex, Cursor, Antigravity e demais) que abrirem este repo. Claude Code tem brief proprio em [`CLAUDE.md`](CLAUDE.md) - o conteudo se sobrepoe muito; leia este se o seu agente seguir a convencao `AGENTS.md`.

## O que e este projeto

`ai-process-pack` e um pack portavel de processo para agentes transformarem pedidos soltos em demandas rastreaveis (backlog, ready, finish) e protegerem arquivos homologados contra refactor de brinde. **Este repo aplica seu proprio processo (dogfood)** - voce trabalha aqui igual trabalharia em qualquer projeto que tenha o pack instalado.

Camadas: skill (interface conversacional) -> script (`core/src/ai.py`, fonte de verdade) -> arquivos JSON/YAML (`.ai/`, `features/registry.yaml`). Detalhe em [`docs/explanation/visao-geral.md`](docs/explanation/visao-geral.md).

Layout do repo-mae: **fontes** em `core/` (src, build, manifest, lock, hooks, templates) e **buildado** em `dist/` (`.claude-plugin/`, `skills/`, `.agents/skills/` - gerados por `python core/build/render-skills.py`). Wrapper `core/bin/ai.ps1` segue como entry point documentado e roteia pra `core/src/ai.py`.

## Regras nao-negociaveis

1. **Toda mutacao de estado passa pelo script.** Nunca edite `.ai/*.json`, `FEATURES.md`, `features/registry.yaml` ou `.ai/chat-title.txt` a mao. Use `core/bin/ai.ps1` (Windows) ou `python core/src/ai.py` (qualquer SO).
2. **Toda demanda nasce de `feature`, `issue` ou `backlog`.** Antes de editar codigo a pedido do usuario, abra a demanda. Sem demanda ativa, nao ha rastreabilidade.
3. **Nao edite arquivos gerados.** `dist/skills/<verbo>/SKILL.md` (output do plugin Claude oficial) e `dist/.agents/skills/<verbo>/SKILL.md` (cross-tool Codex+Antigravity, convencao AGENTS.md) sao saida de `core/build/render-skills.py` a partir de `core/manifest/manifest.yaml`. Mude o manifest e rode `python core/build/render-skills.py`. Edicao direta e sobrescrita na proxima render e quebra o `--check` da CI. `dist/.claude-plugin/plugin.json` so muda pra bump de versao ou ajuste de metadados (name/description/author). Decisao do layout em [`docs/adr/0006-plugin-oficial-claude-code.md`](docs/adr/0006-plugin-oficial-claude-code.md).
4. **Respeite o lock.** `features/registry.yaml` lista arquivos travados. Se voce precisa editar um deles, a mensagem de commit precisa de `[unlock:<feature-id>] motivo: <razao curta>`. Receita: [`docs/how-to/editar-arquivo-travado.md`](docs/how-to/editar-arquivo-travado.md). O hook `commit-msg` rejeita commits sem a marca.
5. **Nao use `--no-verify`** para escapar do hook. Se a trava parece errada, investigue antes - normalmente significa que o usuario nao autorizou aquela edicao.

## Fluxo padrao por turno

1. **Identifique a demanda.** Rode `.\core\bin\ai.ps1 status` para ver a task atual. Se nao houver, abra:
   - Bug: `.\core\bin\ai.ps1 issue "Titulo" --context "Sintoma e impacto"`
   - Capacidade nova: `.\core\bin\ai.ps1 feature "Titulo" --context "Motivo e escopo"`
   - Ideia sem prazo: `.\core\bin\ai.ps1 backlog add "Ideia" --context "Quando pode ser util"`
2. **Repita o NOME DO CHAT.** Todo subcomando que cria ou avanca demanda imprime `NOME DO CHAT: <ID> - #<etapa> - <titulo>`. Voce **deve** ecoar essa linha ao usuario - e o sinal de rastreabilidade entre chat e demanda. Se sua plataforma expoe API de renomeacao de sessao, aplique.
3. **Implemente.** Edicoes normais. Se o arquivo aparecer em `features/registry.yaml`, pare e siga o how-to do unlock.
4. **Marque pronto:**
   ```powershell
   .\core\bin\ai.ps1 ready <ID> `
       --file <caminho> [--file <outro>] `
       --summary "Resumo do que foi feito" `
       --validation "Comando/check executado e resultado"
   ```
5. **Nao feche sozinho.** `finish` so depois de validacao humana em uso real. Test suite passar **nao basta** - o usuario testa de verdade e ai pede o `finish`.
6. **Antes de fechar, rode o docs-check:**
   ```powershell
   .\core\bin\ai.ps1 docs-check
   ```
   Le `.ai/docs-map.yaml` e lista os docs vivos que podem precisar atualizar. Avalie cada candidato, edite o que fizer sentido e feche com `--docs-touched <path>` (repetivel) e/ou `--docs-skip "<motivo>"`. Sem mapa, o passo vira no-op com aviso. Receita em [`docs/how-to/manter-docs-atualizados.md`](docs/how-to/manter-docs-atualizados.md).

## Comandos uteis

| Para que | Comando |
| --- | --- |
| Sanity check do layout | `.\core\bin\ai.ps1 doctor` |
| Ver task atual | `.\core\bin\ai.ps1 status` |
| Ver uma task especifica | `.\core\bin\ai.ps1 status <ID>` |
| Listar backlog | `.\core\bin\ai.ps1 backlog list` |
| Listar docs candidatos a atualizar | `.\core\bin\ai.ps1 docs-check [F-NNN]` |
| Regerar skills | `python core/build/render-skills.py` |
| Conferir drift de skills (CI) | `python core/build/render-skills.py --check` |
| Help geral | `.\core\bin\ai.ps1 --help` |
| Help de subcomando | `.\core\bin\ai.ps1 <sub> --help` |

Reference completa: [`docs/reference/cli.md`](docs/reference/cli.md).

## Convencoes

- **Commits:** `feature: ...`, `issue: ...`, `chore: ...` no imperativo. Exemplos no `git log`. Para arquivo travado: incluir `[unlock:<feature-id>] motivo: <razao>`.
- **Docs:** estrutura Diataxis em `docs/{tutorials,how-to,reference,explanation}/`. Antes de criar arquivo de doc, leia [`docs/explanation/por-que-diataxis.md`](docs/explanation/por-que-diataxis.md).
- **Plataforma alvo:** comandos no README/docs usam PowerShell (`.\core\bin\ai.ps1`). Em Linux/Mac use `python core/src/ai.py <sub>` - o resultado e identico.

## O que nao fazer

- Nao "limpe" arquivos `.ai/*.json` "para reorganizar". O script trata serializacao; mudanca manual quebra o schema.
- Nao reescreva docs antigos sem demanda (`feature` ou `issue`). Mudanca de doc tambem e rastreada.
- Nao introduza dependencias novas em Python sem demanda explicita. Hoje o pack roda com stdlib + `pyyaml`.
- Nao crie LICENSE/CONTRIBUTING/SECURITY/CODE_OF_CONDUCT novos - ja existem na raiz. Edite os existentes.
- Nao sugira `validate` - foi deprecado. Use `ready` -> humano testa -> `finish`.

## Onde aprender mais

- Tutorial guiado: [`docs/tutorials/primeiro-uso.md`](docs/tutorials/primeiro-uso.md)
- Por que o script e fonte de verdade: [`docs/explanation/por-que-script-fonte-da-verdade.md`](docs/explanation/por-que-script-fonte-da-verdade.md)
- Por que travar arquivos: [`docs/explanation/por-que-lock.md`](docs/explanation/por-que-lock.md)
- Como contribuir (para humanos): [`CONTRIBUTING.md`](CONTRIBUTING.md)
