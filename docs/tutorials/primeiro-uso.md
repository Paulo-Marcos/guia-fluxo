# Primeiro uso

Voce vai sair do zero ate ter uma feature criada, implementada e finalizada usando o guia-fluxo.

## Pre-requisito

- Python 3.10+
- Git
- Pack instalado no Claude Code via `/plugin install guia@guia-fluxo` (rota recomendada — o `.guia/` é criado no primeiro comando) **ou** sessao aberta neste repo-mae (dogfood). Cross-tool (Codex/Antigravity) por copia manual. Detalhes em [how-to/instalar-em-outro-projeto.md](../how-to/instalar-em-outro-projeto.md).

## Convencao deste tutorial

Em projeto consumidor (Claude com o plugin instalado, ou cópia manual para Codex/Antigravity), os comandos saem assim:

```powershell
ai <subcomando>            # se .guia-fluxo/bin estiver no PATH (Claude faz auto)
# ou
python .guia-fluxo/bin/guia.py <subcomando>
```

No repo-mae (este repo, dogfood), use o wrapper de fontes:

```powershell
.\core\bin\guia.ps1 <subcomando>
```

A semantica e identica. Os exemplos abaixo usam a forma `.\core\bin\guia.ps1` por default; ajuste para `ai` se voce esta em projeto consumidor.

## 1. Bootstrap do processo

**Em projeto consumidor (Claude):** o motor cria o `.guia/` sozinho no primeiro comando, entao este passo e automatico - pule para o `doctor` no fim desta secao.

**Dogfood (este repo):** o `.guia/` ja existe; tambem pule.

**Se precisar rodar manualmente** (ex.: instalacao copia-manual para Codex/Antigravity):

```powershell
.\core\bin\guia.ps1 init --project-name "meu-projeto"
git config core.hooksPath .githooks
```

O `init` cria:
- `.guia/process.json` com o nome do projeto.
- `.guia/tasks.json`, `.guia/backlog.json`, `.guia/current-task.json` vazios.
- `.guia/chat-title.txt` zerado.

O `core.hooksPath` ativa o hook `commit-msg` que valida marcas `[unlock:<id>]` em commits que tocam arquivos travados. Em projeto consumidor o caminho e `.githooks` (output do instalador); no repo-mae e `core/hooks`.

Confira:

```powershell
.\core\bin\guia.ps1 doctor
```

## 2. Crie sua primeira feature

```powershell
.\core\bin\guia.ps1 feature "Adicionar comando de export" --context "Cliente pediu CSV"
```

Saida tipica:

```
F-001 created: Adicionar comando de export

NOME DO CHAT: F-001 - #DEV - Adicionar comando de export
CHAT_TITLE=F-001 - #DEV - Adicionar comando de export
```

O script:
- Gera o ID `F-001`.
- Atualiza `.guia/tasks.json` e `.guia/current-task.json`.
- Acrescenta a entrada em `FEATURES.md`.
- Imprime e grava em `.guia/chat-title.txt` o titulo sugerido para o chat.

Voce (ou o agente) deve **repetir a linha `NOME DO CHAT: ...` no chat**. Se a ferramenta expor `/rename`, aplique-o. Detalhes por ferramenta: [reference/chat-rename-suporte.md](../reference/chat-rename-suporte.md).

## 3. Implemente

Edite os arquivos do projeto normalmente.

> **Antes de editar qualquer arquivo, confira [`features/registry.yaml`](../reference/registry-yaml.md).** Se o arquivo estiver travado, siga [how-to/editar-arquivo-travado.md](../how-to/editar-arquivo-travado.md).

## 4. Marque como pronta para validacao

```powershell
.\core\bin\guia.ps1 ready F-001 --file scripts/export.py --summary "CLI export criado" --validation "python scripts/export.py --help"
```

Isso move a task para `Aguardando validacao` e gera um relatorio em `.guia/reports/`.

## 5. Valide na pratica

Voce (humano) testa a feature em uso real.

## 6. Finalize

```powershell
.\core\bin\guia.ps1 finish F-001
```

Saida inclui `NOME DO CHAT: F-001 - #FINALIZADO - ...`. Por padrao, `finish` commita as mudancas.

Para travar a feature contra refactor futuro (opcional):

```powershell
.\core\bin\guia.ps1 finish F-001 --lock --lock-id meu-projeto-export
```

## Proximos passos

- [How-to: instalar em outro projeto](../how-to/instalar-em-outro-projeto.md) - plugin global-first no Claude + copia manual cross-tool.
- [How-to: promover backlog para feature/bug/chore](../how-to/promover-backlog.md) - quando voce ja tem uma ideia rascunhada no backlog.
- [Reference: CLI completo](../reference/cli.md) - todas as flags de cada subcomando.
- [Explanation: visao geral do processo](../explanation/visao-geral.md) - entender o papel de cada peca.
