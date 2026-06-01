# AGENTS.md

Briefing para agentes de IA (Codex, Cursor, Antigravity e demais) que abrirem este repo. Claude Code tem brief proprio em [`CLAUDE.md`](CLAUDE.md) - o conteudo se sobrepoe muito; leia este se o seu agente seguir a convencao `AGENTS.md`.

## O que e este projeto

`ai-process-pack` e um pack portavel de processo para agentes transformarem pedidos soltos em demandas rastreaveis (backlog, ready, finish) e protegerem arquivos homologados contra refactor de brinde. **Este repo aplica seu proprio processo (dogfood)** - voce trabalha aqui igual trabalharia em qualquer projeto que tenha o pack instalado.

Camadas: skill (interface conversacional) -> script (`scripts/ai.py`, fonte de verdade) -> arquivos JSON/YAML (`.ai/`, `features/registry.yaml`). Detalhe em [`docs/explanation/visao-geral.md`](docs/explanation/visao-geral.md).

## Regras nao-negociaveis

1. **Toda mutacao de estado passa pelo script.** Nunca edite `.ai/*.json`, `FEATURES.md`, `features/registry.yaml` ou `.ai/chat-title.txt` a mao. Use `scripts/ai.ps1` (Windows) ou `python scripts/ai.py` (qualquer SO).
2. **Toda demanda nasce de `feature`, `issue` ou `backlog`.** Antes de editar codigo a pedido do usuario, abra a demanda. Sem demanda ativa, nao ha rastreabilidade.
3. **Nao edite `skills/generated/*`.** Esses arquivos sao gerados a partir de `skills/manifest.yaml`. Mude o manifest e rode `python scripts/render-skills.py`. Edicao direta e sobrescrita na proxima render e quebra o `--check` da CI.
4. **Respeite o lock.** `features/registry.yaml` lista arquivos travados. Se voce precisa editar um deles, a mensagem de commit precisa de `[unlock:<feature-id>] motivo: <razao curta>`. Receita: [`docs/how-to/editar-arquivo-travado.md`](docs/how-to/editar-arquivo-travado.md). O hook `commit-msg` rejeita commits sem a marca.
5. **Nao use `--no-verify`** para escapar do hook. Se a trava parece errada, investigue antes - normalmente significa que o usuario nao autorizou aquela edicao.

## Fluxo padrao por turno

1. **Identifique a demanda.** Rode `.\scripts\ai.ps1 status` para ver a task atual. Se nao houver, abra:
   - Bug: `.\scripts\ai.ps1 issue "Titulo" --context "Sintoma e impacto"`
   - Capacidade nova: `.\scripts\ai.ps1 feature "Titulo" --context "Motivo e escopo"`
   - Ideia sem prazo: `.\scripts\ai.ps1 backlog add "Ideia" --context "Quando pode ser util"`
2. **Repita o NOME DO CHAT.** Todo subcomando que cria ou avanca demanda imprime `NOME DO CHAT: <ID> - #<etapa> - <titulo>`. Voce **deve** ecoar essa linha ao usuario - e o sinal de rastreabilidade entre chat e demanda. Se sua plataforma expoe API de renomeacao de sessao, aplique.
3. **Implemente.** Edicoes normais. Se o arquivo aparecer em `features/registry.yaml`, pare e siga o how-to do unlock.
4. **Marque pronto:**
   ```powershell
   .\scripts\ai.ps1 ready <ID> `
       --file <caminho> [--file <outro>] `
       --summary "Resumo do que foi feito" `
       --validation "Comando/check executado e resultado"
   ```
5. **Nao feche sozinho.** `finish` so depois de validacao humana em uso real. Test suite passar **nao basta** - o usuario testa de verdade e ai pede o `finish`.
6. **Antes de fechar, rode o docs-check:**
   ```powershell
   .\scripts\ai.ps1 docs-check
   ```
   Le `.ai/docs-map.yaml` e lista os docs vivos que podem precisar atualizar. Avalie cada candidato, edite o que fizer sentido e feche com `--docs-touched <path>` (repetivel) e/ou `--docs-skip "<motivo>"`. Sem mapa, o passo vira no-op com aviso. Receita em [`docs/how-to/manter-docs-atualizados.md`](docs/how-to/manter-docs-atualizados.md).

## Comandos uteis

| Para que | Comando |
| --- | --- |
| Sanity check do layout | `.\scripts\ai.ps1 doctor` |
| Ver task atual | `.\scripts\ai.ps1 status` |
| Ver uma task especifica | `.\scripts\ai.ps1 status <ID>` |
| Listar backlog | `.\scripts\ai.ps1 backlog list` |
| Listar docs candidatos a atualizar | `.\scripts\ai.ps1 docs-check [F-NNN]` |
| Regerar skills | `python scripts/render-skills.py` |
| Conferir drift de skills (CI) | `python scripts/render-skills.py --check` |
| Help geral | `.\scripts\ai.ps1 --help` |
| Help de subcomando | `.\scripts\ai.ps1 <sub> --help` |

Reference completa: [`docs/reference/cli.md`](docs/reference/cli.md).

## Convencoes

- **Commits:** `feature: ...`, `issue: ...`, `chore: ...` no imperativo. Exemplos no `git log`. Para arquivo travado: incluir `[unlock:<feature-id>] motivo: <razao>`.
- **Docs:** estrutura Diataxis em `docs/{tutorials,how-to,reference,explanation}/`. Antes de criar arquivo de doc, leia [`docs/explanation/por-que-diataxis.md`](docs/explanation/por-que-diataxis.md).
- **Plataforma alvo:** comandos no README/docs usam PowerShell (`.\scripts\ai.ps1`). Em Linux/Mac use `python scripts/ai.py <sub>` - o resultado e identico.

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
