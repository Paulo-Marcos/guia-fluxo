# Configurar a entrega num projeto

Use quando for ligar o fluxo por PR num projeto, ou quando atualizar o plugin e quiser ver o que
mudou. Nao edite o `.guia/process.json` a mao: o configurador explica cada decisao e grava com
backup. O fluxo inteiro esta em [O fluxo de entrega, de ponta a ponta](../explanation/fluxo-de-entrega.md).

## No chat

```text
/guia:configure
```

O agente pergunta se voce quer todas as etapas ou so as pendentes e conduz uma decisao por vez:
o que se decide, o que o Guia viu no projeto, o valor atual e a recomendacao com o porque. No
fim mostra o resumo `antes -> depois` e so grava com o seu ok. E um comando so do usuario: o
agente nao o dispara sozinho, porque ele mexe na autonomia.

## No terminal

```powershell
python "$env:USERPROFILE\.claude\plugins\cache\guia-fluxo\guia\<versao>\bin\guia.py" configure
```

Uma etapa por vez: **Enter** aceita a recomendada, um **numero** escolhe a opcao, **m** mantem o
atual, **q** sai sem gravar, ou digite o valor (listas separadas por virgula). No fim,
`Gravar? [s/N]`. Para ver so o que falta decidir ou difere da recomendacao, acrescente
`--pendentes`.

## Sem perguntas

```powershell
guia configure --plan                        # todas as etapas, explicadas
guia configure --set mode=pr --set gate=...  # simula: mostra o que mudaria
guia configure --set mode=pr --yes           # grava (anterior em .guia/backups/)
```

## Depois de gravar

- As linhas **"Fora do process.json"** sao com voce: protecao da branch
  (`guia scaffold protection`), workflow de auditoria (`guia scaffold auditoria`), script de
  release compilando os fragmentos.
- Conferir que a configuracao bate com o GitHub: `guia doctor --delivery`.
- Errou? O arquivo anterior esta em `.guia/backups/process.json.<data-hora>`.
