# Como configurar hooks git

## Instalacao (uma vez por clone)

```powershell
git config core.hooksPath .githooks
```

Isso aponta o git deste repositorio para os hooks versionados em `.githooks/`. Como os hooks ficam no controle de versao, qualquer clone que rode o comando acima passa a usa-los.

> Este passo e **por clone**. Se voce (ou outra pessoa) clonar o repo de novo, refaca.

## Verificar que esta ativo

```powershell
git config --get core.hooksPath
```

Deve imprimir `.githooks`.

## Dependencia do hook

O `commit-msg` chama `python bin/check-lock.py`. Requer Python 3.8+ e `pyyaml`:

```powershell
pip install pyyaml
```

## Bypass em emergencia

```powershell
git commit --no-verify -m "..."
```

Nao recomendado: o workflow `.github/workflows/lock-check.yml` re-checa no PR e barra o merge de qualquer jeito.

## Detalhes do que cada hook faz

Ver [reference/hooks-git.md](../reference/hooks-git.md).

## Troubleshooting

Hook nao bloqueia ou nao roda? Ver [reference/troubleshooting.md](../reference/troubleshooting.md).
