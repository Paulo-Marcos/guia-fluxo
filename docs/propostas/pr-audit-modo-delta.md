# Proposta: `pr-audit` com procedência por patch-id e modo delta

**Para:** a skill `pr-audit` em `C:\DEV\my-skills\pr-audit` (repositório
`my-skills`, dono: Paulo). **Daqui não se edita o `my-skills`** (R8 da
especificação): este documento e o patch ao lado são a proposta; aplicar é
decisão do dono.

**Patch:** [`pr-audit-modo-delta.patch`](pr-audit-modo-delta.patch), contra
`pr-audit/SKILL.md` no commit `9ec2cc1` do `my-skills` (blob `9f83b96`).
Aplica limpo com fim de linha LF ou CRLF:

```powershell
cd C:\DEV\my-skills
git apply --check C:\DEV\guia-fluxo\docs\propostas\pr-audit-modo-delta.patch
git apply C:\DEV\guia-fluxo\docs\propostas\pr-audit-modo-delta.patch
```

## O problema

Hoje a Fase 6, item 3, manda: **"Head novo → repita a Fase 2 no diff
inteiro"**. Com a fila do Guia isso pesa duas vezes:

- a proteção `strict` obriga o PR a estar em dia com a `main`; cada merge
  deixa os outros PRs atrás, e o rebase cria um head novo **sem mudar o que o
  PR faz**;
- quando o rebase muda algo (um conflito resolvido), a mudança costuma ser de
  poucas linhas, mas a skill pede a releitura do diff inteiro.

## O que o Guia já faz (motor)

- **Carga por patch-id (Onda 4, R8):** o executor compara
  `git diff <merge-base>..<head> | git patch-id --verbatim` do head aprovado e
  do novo. Igual, comenta o marcador do head novo com
  `carry-from=<sha antigo> patch-id=<id>`, e o `auditoria.yml` grava o status.
- **Delta (D-140):** diferente, o executor devolve o PR pedindo auditoria de
  delta; o `guia audit` grava a base auditada, imprime
  `git range-diff <base-velha>..<head-velho> <base-nova>..<head-novo>` e
  registra `audit.mode = delta`.

Falta a skill saber disso: sem a mudança, ela reaudita tudo mesmo quando o
motor já provou que nada mudou.

## A mudança na skill

1. **Nova seção "Head novo depois da aprovação"**, entre a Fase 4 e as
   Severidades:
   - *Procedência por patch-id:* os dois comandos, com `--verbatim` e o porquê
     (o `--stable` ignora espaço em branco; indentação em Python muda
     comportamento). Iguais → a aprovação vale para o head novo, com a linha
     de procedência; nada a reauditar.
   - *Modo delta:* os quatro SHAs fixados e o `range-diff`. Fase 2 no delta
     (commits novos ou alterados e mudanças de contexto), com as checagens
     mecânicas (`--check`, travas, padrão de commit) no intervalo **inteiro**;
     Fase 3 **inteira** no head novo, sempre ("o delta reduz a leitura, não a
     execução"); Fase 4 no que mudou e onde ele toca o aprovado.
   - *Volta à auditoria completa* quando o range-diff não se lê com segurança,
     o delta toca workflows, `AGENTS.md`, travas, `.claude/settings.json` ou
     dependências, a aprovação anterior não foi do dono, ou falta um SHA.
2. **Fase 0:** um parágrafo apontando a seção nova para quem chega com um
   head novo.
3. **Relatório (Fase 5):** a linha
   `Modo: completo | delta desde <SHA aprovado> (git range-diff ..., relatório original: <link>)`.
4. **Fase 6, item 3:** troca "repita a Fase 2 no diff inteiro" pelo caminho
   novo (patch-id igual carrega; diferente, Fases 2 e 4 no delta e o portão
   completo uma vez).

## O que não muda

A fronteira de confiança, o livro de alegações, o portão hostil, a execução
isolada e a assimetria das dúvidas ficam como estão. O delta só decide **o
que ler** de novo; a execução do portão e o marcador por head continuam
obrigatórios, e qualquer dúvida devolve à auditoria completa.

## Como validar depois de aplicar

No próximo PR que o executor devolver por patch-id diferente: rodar a
`pr-audit` com o `range-diff` que o `guia audit` imprime, conferir que o
relatório traz a linha `Modo: delta desde ...` e que o portão completo rodou
no head novo.
