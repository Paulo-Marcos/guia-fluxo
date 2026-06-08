# Reference: troubleshooting

## "PyYAML nao instalado"

```powershell
pip install pyyaml
```

## O hook nao roda

```powershell
git config --get core.hooksPath
```

Deve imprimir `core/hooks`. Se vazio:

```powershell
git config core.hooksPath core/hooks
```

## O hook roda mas nao bloqueia

Verifique se `core/hooks/commit-msg` esta acessivel e se `core/lock/check-lock.py` retorna erro 1 para um arquivo travado:

```powershell
python core/lock/check-lock.py check <arquivo-que-deveria-estar-travado>
echo $LASTEXITCODE   # esperado: 1
```

## CI passa mas eu queria que bloqueasse o merge

O workflow precisa estar listado em **Branch protection rules -> Required status checks** no GitHub. Sem isso, o CI roda mas o merge passa.

## Commitei sem `[unlock:...]` e o hook bloqueou

```powershell
git commit --amend
# editor abre, adicione a linha [unlock:<id>] motivo: ..., salve, feche
```

Se ja tinha pushed em PR, faca um novo commit com a marca (ou amend + force-push se for branch privado seu).

## "guia.ps1 nao encontrado" no PowerShell

Voce esta em outro diretorio. Use caminho absoluto ou:

```powershell
cd C:\caminho\do\projeto
.\core\bin\guia.ps1 status
```

## "Python not found" ao invocar `guia.ps1`

```powershell
$env:GUIA_PYTHON = "C:\caminho\para\python.exe"
.\core\bin\guia.ps1 doctor
```

Ou instale Python 3.10+ em local conhecido (o wrapper tenta `python`, `python3`, `py`, `%LOCALAPPDATA%\Programs\Python\Python313\python.exe` e a venv do repo).

## Skills geradas divergem do manifest

```powershell
python core/build/render-skills.py --check
```

Se sair com erro, rode sem `--check` para regenerar:

```powershell
python core/build/render-skills.py
```
