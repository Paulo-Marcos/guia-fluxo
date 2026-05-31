# Por que Diataxis

## O problema anterior

Os tres documentos originais (`AI_PROCESS.md`, `PROTOCOL.md`, `HOOKS.md`) misturavam tudo:

- `AI_PROCESS.md` (220 linhas) tinha visao geral + tutorial + lista de comandos + protocolo de promote + protocolo de chat rename + protocolo de hooks + roadmap.
- `PROTOCOL.md` (358 linhas) tinha explicacao de por que travar + tutorial de setup + how-to de varios casos + reference do schema + troubleshooting.
- `HOOKS.md` (28 linhas) era so reference, mas isolado.

Sintomas:

- Quem queria a sintaxe exata do `finish` precisava ler 220 linhas.
- Quem queria entender por que existe lock encontrava a explicacao misturada com tutorial de setup.
- Quem queria so configurar o hook tinha que adivinhar onde a info estava.
- Adicionar conteudo novo era pior: nao havia lugar obvio para colocar.

## O framework

[Diataxis](https://diataxis.fr/) (criado pela equipe de docs do Django, adotado por Cloudflare, GitLab, Gatsby) diz que toda documentacao tecnica serve a **quatro propositos distintos** que nao devem se misturar:

| Quadrante | Audiencia | Pergunta |
| --- | --- | --- |
| Tutorial | Iniciante | "Me leve do zero a um resultado funcionando" |
| How-to | Usuario com problema especifico | "Como faco X?" |
| Reference | Quem precisa consultar | "Qual a sintaxe exata?" |
| Explanation | Quem quer entender | "Por que e assim?" |

A regra de ouro: um documento que tenta ser dois quadrantes ao mesmo tempo falha em todos.

## A separacao com README e CHANGELOG

Diataxis governa **so o conteudo de `docs/`**. Nao se confunde com:

- `README.md` (raiz) - elevator pitch + install + link para `docs/tutorials/primeiro-uso.md`. Porta de entrada do projeto.
- `CHANGELOG.md` (raiz) - historico cronologico de versoes. Para quem ja usa e precisa decidir se atualiza.
- `ROADMAP.md` - planejamento de versoes. Continua em `docs/` por convencao, mas nao e Diataxis (e planejamento de projeto, nao documentacao de uso).

## O que foi feito

| Antes | Depois |
| --- | --- |
| `docs/AI_PROCESS.md` | Fatiado em [tutorials/primeiro-uso](../tutorials/primeiro-uso.md), [reference/cli](../reference/cli.md), [reference/files](../reference/files.md), [how-to/renomear-chat](../how-to/renomear-chat.md), [how-to/promover-backlog](../how-to/promover-backlog.md), [reference/chat-rename-suporte](../reference/chat-rename-suporte.md), [explanation/visao-geral](visao-geral.md) |
| `docs/PROTOCOL.md` | Fatiado em [explanation/por-que-lock](por-que-lock.md), [explanation/convencoes-de-lock](convencoes-de-lock.md), [reference/registry-yaml](../reference/registry-yaml.md), [how-to/travar-arquivo](../how-to/travar-arquivo.md), [how-to/editar-arquivo-travado](../how-to/editar-arquivo-travado.md), [how-to/destravar-arquivo](../how-to/destravar-arquivo.md), [how-to/renomear-arquivo-travado](../how-to/renomear-arquivo-travado.md), [how-to/auditar-desbloqueios](../how-to/auditar-desbloqueios.md), [reference/troubleshooting](../reference/troubleshooting.md) |
| `docs/HOOKS.md` | Fatiado em [reference/hooks-git](../reference/hooks-git.md) e [how-to/configurar-hooks-git](../how-to/configurar-hooks-git.md) |
| `docs/INSTALL.md` | Movido para [how-to/instalar-em-outro-projeto](../how-to/instalar-em-outro-projeto.md) (e how-to: "como faco para instalar?"). |

## Beneficio esperado

- Quem entra hoje vai ate [tutorials/primeiro-uso.md](../tutorials/primeiro-uso.md) e em 5 minutos tem uma feature finalizada.
- Quem tem um problema especifico ("como travo um arquivo?") vai direto no [how-to](../how-to/).
- Quem precisa da sintaxe vai no [reference](../reference/) sem ler prosa.
- Quem questiona uma decisao tem [explanation](.) com contexto - e nao polui o reference com discussao.

## Custo

- Mais arquivos (4 pastas, ~20 arquivos vs 4 monolitos).
- Disciplina para nao misturar quadrantes quando adicionar conteudo novo.

Para o tamanho deste projeto, o tradeoff vale: cada arquivo individual e pequeno e responde uma pergunta clara.
