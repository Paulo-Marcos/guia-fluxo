# Como renomear (ou mover) um arquivo travado

Tratado como edicao. Use unlock temporario **e** atualize o registry.

## Passos

```powershell
# 1. Faca o git mv e commit com [unlock:...]
git mv backend/app/services/ingestao.py backend/app/services/livestream_ingestao.py
git commit -m "refactor: renomeia ingestao para livestream_ingestao

[unlock:ingestao-livestream] motivo: nome mais especifico"

# 2. Atualize o registry para apontar para o novo caminho
python bin/check-lock.py unlock ingestao-livestream
python bin/check-lock.py lock ingestao-livestream `
    --description "Download e parse de VTT da livestream" `
    backend/app/services/livestream_ingestao.py `
    backend/app/domain/vtt_parser.py
```

## Por que dois passos

A trava em `registry.yaml` referencia caminhos. Renomear o arquivo sem atualizar o registry deixa a entrada apontando para um path inexistente - silenciosamente nada fica protegido.

## Adicionar arquivo novo a uma feature ja travada

A trava nao impede criar arquivos novos em outros caminhos. Para incluir o novo arquivo na protecao:

```powershell
python bin/check-lock.py unlock ingestao-livestream
python bin/check-lock.py lock ingestao-livestream `
    --description "Download e parse de VTT" `
    backend/app/services/ingestao.py `
    backend/app/domain/vtt_parser.py `
    backend/app/domain/vtt_validator.py   # novo
```
