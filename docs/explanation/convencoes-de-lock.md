# Convencoes de lock

## Granularidade

Trave por **feature de negocio**, nao por arquivo solto. Uma trava deve agrupar tudo que compoe a funcionalidade:

- Servico de dominio: `backend/app/services/<feature>.py`
- Utilitarios de dominio relacionados: `backend/app/domain/<modulo>.py`
- Router que expoe a feature: `backend/app/routers/<feature>.py`
- Testes: `backend/tests/test_<feature>.py`
- Componente React que consome (se a UI for parte do contrato)

Trava por arquivo isolado costuma indicar que voce ainda nao identificou a feature - revisite o escopo.

## Nomes (id)

- **kebab-case**, slug curto: `ingestao-livestream`, `export-losslesscut`.
- Use o vocabulario do dominio (`Ingestao`, `Export`, `Analise`, `Corte`).
- Evite nomes genericos (`servico-backend`, `helper`, `util`) - falham em descrever o que esta protegido. Quem ler `[unlock:helper]` em um commit daqui a 6 meses nao vai saber o que isso significa.

## Quando travar

Trave quando:

- A feature foi **testada** (mesmo que com smoke test manual) e esta em uso real.
- Nao ha bug aberto conhecido nela.
- Voce nao planeja iterar nela no curto prazo.

## Quando NAO travar

- Codigo em construcao (mude livremente).
- Codigo que voce sabe que vai refatorar essa semana.
- Configuracao que muda demais (`.env`, `*.config.js`).
- Arquivos de migracao de banco (sao append-only por natureza).

## Casos especiais

### Refactor que atravessa uma feature travada

Se um refactor maior precisa mexer numa feature travada **e em outras coisas**:

- **Opcao A (preferida):** faca o refactor em PR separado, so com o necessario, usando unlock temporario.
- **Opcao B:** aceite o unlock no PR maior, com motivo descritivo.

```
refactor: extrai cliente HTTP comum entre servicos

[unlock:ingestao-livestream] motivo: trocar requests por httpx
```

### Renomear ou mover arquivo travado

Tratado como edicao. Ver [how-to/renomear-arquivo-travado.md](../how-to/renomear-arquivo-travado.md).

### Adicionar arquivo novo a uma feature travada

A trava nao impede criar arquivos novos em outros caminhos. Isso significa que e facil um agente "estender" a feature por fora - **comportamento explicitamente proibido** (renomear, dividir, recriar logica equivalente noutro lugar).

Se voce quer mesmo estender a feature, atualize o registry para incluir o novo arquivo. Ver [how-to/renomear-arquivo-travado.md#adicionar-arquivo-novo-a-uma-feature-ja-travada](../how-to/renomear-arquivo-travado.md#adicionar-arquivo-novo-a-uma-feature-ja-travada).

### Trava colidiu com algo que voce esqueceu

Acontece. Use `[unlock:<id>] motivo: ...` no commit e siga. A trava **nao e camisa de forca** - e um pedido consciente de pausa para voce confirmar que sabe o que esta mexendo.

## Emergencia (nao recomendado)

Para bypass total do hook local:

```powershell
git commit --no-verify -m "..."
```

Mas o **CI ainda vai pegar** no PR. Para realmente forcar, voce precisaria desabilitar a branch protection no GitHub - o que e deliberado e visivel no historico.
