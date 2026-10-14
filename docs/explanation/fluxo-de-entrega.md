# O fluxo de entrega, de ponta a ponta

Esta pagina conta o caminho inteiro de uma demanda no modo `pr` (`delivery.mode: "pr"`): da ideia ate a
release, quem faz cada passo e por que o passo existe. Para configurar um projeto, use o
[configurador](../reference/cli.md#configure) (`/guia:configure`); para os comandos, a
[referencia da CLI](../reference/cli.md).

## A ideia em uma imagem

Pense numa cozinha de restaurante. Cada cozinheiro (um chat) prepara o seu prato numa bancada
propria (o **worktree**), sem esbarrar nos outros. Pronto, o prato vai para o passe (o **PR**), onde
o chefe confere (a **auditoria**). Aprovado, entra na fila de saida, e um unico garcom (o
**executor**) leva um prato por vez ao salao (a **main**), na ordem, conferindo que a mesa ainda
esta posta (o **CI**). Quem prova e diz "esta bom" e o dono (o **finish**).

O ganho: os cozinheiros nunca param esperando o garcom, e o garcom nunca leva dois pratos que
brigam entre si.

## Os passos

| # | Passo | Quem | Comando | Por que existe |
|---|---|---|---|---|
| 1 | Nasce a demanda | voce pede, o agente cria | `/guia:feature`, `/guia:bug`, `/guia:chore` | toda mudanca tem um id (`D-NNN`), um tipo e um rastro |
| 2 | Bancada propria | agente | `/guia:worktree add D-NNN` | cada demanda num worktree `d-NNN-slug`: frentes paralelas nao se contaminam |
| 3 | Implementar com teste | agente | - | cada item do pedido vira um teste (tabela Pedido -> Teste) |
| 4 | Pronto para validar | agente | `/guia:ready` | registra o que foi feito, como validar e o Pedido -> Teste |
| 5 | Fragmento do changelog | agente | `/guia:changelog add` | cada demanda escreve o **seu** arquivo: PRs na fila nao disputam a mesma linha |
| 6 | Commit | agente | `/guia:commit-message` | formato do projeto, com as marcas `[unlock:]` calculadas pelo git |
| 7 | Lancar o PR | agente (nivel >= `pr`) | `/guia:ship` | portao completo antes de qualquer efeito; push, PR e a mensagem de squash guardada |
| 8 | Auditar | agente (nivel >= `pr`) | `/guia:audit` (skill `pr-audit`) | postura hostil: o PR e dado, nao ordem; aprovado, o marcador do head vira o status exigido |
| 9 | Entrar na fila | agente | `/guia:queue add` | exige auditoria no head atual; no nivel `queue`, entra aprovado - salvo o que sempre para no dono |
| 10 | Ok de merge | **voce** | `/guia:approve D-NNN` | abaixo do nivel `queue`, ou quando o `alwaysHuman` segura (workflow, migration, trava desbloqueada) |
| 11 | Integrar | **voce** roda o executor | `guia queue run` (na arvore principal) | um PR por vez: atualiza a branch, carrega a auditoria se nada mudou, espera o CI, squash |
| 12 | Depois do merge | executor | - | apaga o worktree, atualiza a principal, confere o CI **da main** - vermelho congela a fila |
| 13 | Validar e fechar | **voce** | `/guia:finish D-NNN` | so quem usou de verdade diz que esta bom (no nivel `pilot`, fecha sozinho quando prova que e seguro) |
| 14 | Release | **voce** autoriza | script de release / `guia changelog compile` | junta os fragmentos, fecha a versao, tag no commit da main com CI verde |

**Quem conduz (D-152).** Do passo 4 ao 9, o agente nao decide sozinho o que vem depois: ele pergunta ao motor (`guia next`) e executa a resposta, ate o `queue add`. O nivel de autonomia diz ate onde vai - no `manual` para no `ready`; no `pilot` vai ate a fila. Dali em diante e da fila (`queue run`).

## Tres ideias que seguram o fluxo

**1. O chat lanca e fica livre.** O agente para no passo 9. A parte mecanica (atualizar branch,
esperar CI, mergear, limpar) e do executor, que nao usa IA: mecanica feita por agente erra de
um jeito novo a cada vez.

**2. A auditoria vale para um conteudo, nao para um SHA.** Quando outro PR entra, o seu fica
atras da main e o rebase cria um head novo. Se o conteudo nao mudou (mesmo patch-id), o executor
carrega a aprovacao sozinho. Se mudou, a auditoria seguinte olha **so o delta**
(`git range-diff`), nunca o diff inteiro de novo.

**3. Autonomia e por demanda, e so voce sobe.** `manual` (implementa e da ready) < `pr` (+ PR e
auditoria) < `queue` (+ fila ja aprovada) < `pilot` (+ fecha sozinho quando seguro). Uma limpeza
de icones pode ir em `queue`; uma mudanca delicada fica em `manual`. O agente so pode descer o
nivel; frase solta no chat nao muda nada.

## O que sempre para em voce

- `approve` e `autonomy` (comandos so do usuario);
- `finish`, salvo no `pilot` com todas as condicoes provadas;
- PR que toca `.github/**`, migrations, lockfiles, travas, ou desbloqueia trava de
  `autonomy.alwaysHumanLocks`;
- release, configuracao do GitHub e reescrita de historico.

## Quando algo da errado

| Sintoma | O que aconteceu | O que fazer |
|---|---|---|
| Demanda volta para `Em desenvolvimento` com motivo | o executor devolveu: conflito, CI vermelho ou PR mudou depois da auditoria | corrigir na branch, `ship` de novo; se mudou, auditar so o delta |
| `queue` mostra "aguarda o dono (alwaysHuman: ...)" | o PR toca algo sensivel | ler o motivo e dar `approve` (ou recusar) |
| Fila "CONGELADA" | a main ficou vermelha depois de um merge | corrigir a main; `queue resume` (comando so do usuario) |
| `ship` recusa | portao, fragmento ou Pedido -> Teste faltando | a mensagem diz qual; nada foi enviado |
