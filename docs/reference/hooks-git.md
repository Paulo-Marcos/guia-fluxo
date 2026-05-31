# Reference: hooks git

## Hooks disponiveis

### `commit-msg`

Valida travas declaradas em [`features/registry.yaml`](registry-yaml.md). Rejeita commits que modifiquem arquivos travados sem a marca `[unlock:<feature-id>] motivo: <razao>` na mensagem.

Implementacao: chama `python bin/check-lock.py`.

## Instalacao

```powershell
git config core.hooksPath .githooks
```

Por clone (nao fica em commit). Ver [how-to/configurar-hooks-git.md](../how-to/configurar-hooks-git.md).

## Bypass

```powershell
git commit --no-verify
```

Nao recomendado. O workflow `.github/workflows/lock-check.yml` re-checa no PR e barra o merge de qualquer jeito.

## Dependencia

- Python 3.8+.
- `pyyaml` (`pip install pyyaml`).

## Hooks futuros (nao implementados)

O pack atualmente expoe apenas `commit-msg`. Hooks adicionais sao opcionais e devem ser tratados como guarda-corpo, nao como substituto do script:

- `UserPromptSubmit`: lembrar de rodar `/feature` ou `/issue` se nao houver task ativa.
- `PreToolUse`: checar `features/registry.yaml` antes de editar.
- `PostToolUse`: sugerir registrar arquivos na demanda atual.
- `Stop`: avisar se houve mudanca sem `/ready` ou sem `finish`.

Use hooks primeiro em modo aviso. So depois torne bloqueante.

## Camadas de defesa

O `commit-msg` e a **camada local**. O CI (`.github/workflows/lock-check.yml`) e a **camada remota**. Ver [explanation/por-que-lock.md](../explanation/por-que-lock.md) para a logica das tres camadas.
