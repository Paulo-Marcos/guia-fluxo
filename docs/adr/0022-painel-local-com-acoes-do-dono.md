# ADR-0022: Painel local com acoes do dono

- **Status:** Aceita
- **Data:** 2026-10-20

## Contexto

O `guia dashboard` (D-175) nasceu somente leitura: um servidor HTTP so em `127.0.0.1` que mostra, de todos os projetos da maquina, as demandas por etapa e a fila de integracao, inclusive se o executor esta vivo (lease com batimento, D-127) e se a fila esta pausada ou congelada. Para agir sobre o que via, o dono ainda precisava abrir um terminal em cada projeto e rodar `guia queue resume` ou `guia queue run`.

O dono pediu (D-187) que o painel faca essas duas coisas. Isso transforma um servidor local de leitura num ponto de escrita - e uma pagina qualquer aberta no mesmo navegador pode mandar pedidos para `127.0.0.1` (CSRF) ou chegar nele por um nome que resolve para la (DNS rebinding). As duas acoes sao "so do usuario" (`queue-control`): o agente nunca as dispara.

## Decisao

O painel ganha duas acoes, `POST /api/action/queue-resume` e `POST /api/action/queue-run`, mostradas como botoes so quando fazem sentido (fila parada; ou modo `pr`, fila andando e nenhum executor vivo). Nenhuma delas grava estado pelo painel: cada uma roda o proprio motor dentro do projeto (`GUIA_PROJECT_ROOT`), e so para projetos do cadastro. O `queue run` sobe em processo destacado e a unicidade do executor continua sendo a do lease (`O_EXCL`).

O pedido de escrita so passa por quatro portoes, todos obrigatorios:

1. **Host** `127.0.0.1:<porta>` ou `localhost:<porta>` - fecha o DNS rebinding.
2. **Origin** exatamente o do painel - fecha a pagina de outra origem (o navegador sempre manda `Origin` num POST).
3. **`Content-Type: application/json`** - um formulario simples nao consegue mandar, e um `fetch` de outra origem com esse tipo exige preflight, que o painel nao responde.
4. **Token da sessao do painel** no cabecalho `X-Guia-Token`, comparado em tempo constante - gerado a cada `guia dashboard` e embutido na pagina, que outra origem nao consegue ler.

A pagina recusa ser emoldurada (`X-Frame-Options: DENY`, `frame-ancestors 'none'`) e cada botao pede confirmacao, para o clique ser do dono e nao de uma pagina por cima.

## Consequencias

- + O dono retoma a fila e liga o executor sem terminal, vendo todos os projetos.
- + O estado continua mudando so pelo motor (ADR-0001); o painel decide apenas se o botao aparece.
- + Dois cliques (ou duas abas) nao criam dois executores: o painel serializa o disparo e o lease recusa o segundo de qualquer forma.
- - O painel deixa de ser "somente leitura" no sentido estrito; a superficie de ataque local cresce e passa a depender dos quatro portoes - mexer neles exige rever este ADR.
- - O executor iniciado pelo painel roda sem terminal: a saida vai para `.guia/queue/executor-painel.log`, nao para a tela.
- - A trava "so do usuario" continua comportamental: um agente com acesso ao navegador poderia clicar. A regra escrita (o agente nunca usa os botoes) e a confirmacao sao o limite, o mesmo da D-098.

## Alternativas consideradas

- **Gravar `queue.json` direto do servidor.** Mais simples, mas duplicaria a logica de `queue resume` (que tambem descongela, D-128) e quebraria a regra de o estado mudar so pelo motor.
- **So checagem de Origin, sem token.** Suficiente para os navegadores atuais, mas o token custa pouco e cobre cliente que omite ou forja `Origin` sem ter carregado a pagina.
- **Rodar o executor dentro do processo do painel.** Fecharia o painel e mataria o executor no meio de um merge; o processo destacado sobrevive e o lease ja resolve a unicidade.

## Links

- `docs/especificacao-entrega-por-pr.md`, R4 (comandos) e R5 (fila e executor).
- `core/src/_cli_dashboard.py` (portoes), `core/src/_dashboard_actions.py` (acoes).
- ADR-0001 (script fonte da verdade).
