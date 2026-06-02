# Primeiro uso

Voce vai sair do zero ate ter uma feature criada, implementada e finalizada usando o ai-process-pack.

## Pre-requisito

- Python 3.10+
- Git
- Repositorio clonado

## 1. Bootstrap do processo

No diretorio do projeto consumidor:

```powershell
.\core\bin\ai.ps1 init --project-name "meu-projeto"
git config core.hooksPath core/hooks
```

O `init` cria:
- `.ai/process.json` com o nome do projeto.
- `.ai/tasks.json`, `.ai/backlog.json`, `.ai/current-task.json` vazios.
- `.ai/chat-title.txt` zerado.

O `core.hooksPath` ativa o hook `commit-msg` que valida marcas `[unlock:<id>]` em commits que tocam arquivos travados.

Confira:

```powershell
.\core\bin\ai.ps1 doctor
```

## 2. Crie sua primeira feature

```powershell
.\core\bin\ai.ps1 feature "Adicionar comando de export" --context "Cliente pediu CSV"
```

Saida tipica:

```
F-001 created: Adicionar comando de export

NOME DO CHAT: F-001 - #DEV - Adicionar comando de export
CHAT_TITLE=F-001 - #DEV - Adicionar comando de export
```

O script:
- Gera o ID `F-001`.
- Atualiza `.ai/tasks.json` e `.ai/current-task.json`.
- Acrescenta a entrada em `FEATURES.md`.
- Imprime e grava em `.ai/chat-title.txt` o titulo sugerido para o chat.

Voce (ou o agente) deve **repetir a linha `NOME DO CHAT: ...` no chat**. Se a ferramenta expor `/rename`, aplique-o. Detalhes por ferramenta: [reference/chat-rename-suporte.md](../reference/chat-rename-suporte.md).

## 3. Implemente

Edite os arquivos do projeto normalmente.

> **Antes de editar qualquer arquivo, confira [`features/registry.yaml`](../reference/registry-yaml.md).** Se o arquivo estiver travado, siga [how-to/editar-arquivo-travado.md](../how-to/editar-arquivo-travado.md).

## 4. Marque como pronta para validacao

```powershell
.\core\bin\ai.ps1 ready F-001 --file scripts/export.py --summary "CLI export criado" --validation "python scripts/export.py --help"
```

Isso move a task para `Aguardando validacao` e gera um relatorio em `.ai/reports/`.

## 5. Valide na pratica

Voce (humano) testa a feature em uso real.

## 6. Finalize

```powershell
.\core\bin\ai.ps1 finish F-001
```

Saida inclui `NOME DO CHAT: F-001 - #FINALIZADO - ...`. Por padrao, `finish` commita as mudancas.

Para travar a feature contra refactor futuro (opcional):

```powershell
.\core\bin\ai.ps1 finish F-001 --lock --lock-id meu-projeto-export
```

## Proximos passos

- [How-to: registrar bug em vez de feature](../how-to/promover-backlog.md) - quando voce ja tem uma ideia rascunhada no backlog.
- [Reference: CLI completo](../reference/cli.md) - todas as flags de cada subcomando.
- [Explanation: visao geral do processo](../explanation/visao-geral.md) - entender o papel de cada peca.
