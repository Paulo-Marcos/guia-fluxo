# Contribuindo com o ai-process-pack

Obrigado por considerar contribuir. Este projeto e um pack de processo: skill, script (`scripts/ai.py`, fonte de verdade), arquivos JSON/YAML de estado e hooks. As regras abaixo refletem essa arquitetura - se algo aqui parecer inesperado, leia antes [`docs/explanation/visao-geral.md`](docs/explanation/visao-geral.md) e [`docs/explanation/por-que-script-fonte-da-verdade.md`](docs/explanation/por-que-script-fonte-da-verdade.md).

## Pre-requisitos

- Python 3.8+ no PATH.
- `pyyaml` (`pip install pyyaml`) - usado pelo hook `commit-msg` e pelo render.
- Git 2.30+ (para `core.hooksPath`).
- PowerShell 5.1+ (Windows) **ou** Bash equivalente para invocar `scripts/ai.ps1`/`scripts/ai.py` diretamente.

## Setup local

Clone, instale os hooks e rode o doctor:

```powershell
git clone <url>
cd ai-process-pack
git config core.hooksPath .githooks
.\scripts\ai.ps1 doctor
```

`doctor` deve sair com codigo 0. Se falhar, ele aponta o que esta faltando.

## Fluxo de trabalho

Toda contribuicao passa pelo proprio processo do pack (dogfooding). Nao edite `.ai/*.json` nem `FEATURES.md` a mao - quem altera e o script.

1. **Abra uma demanda.**
   - Bug ou regressao: `.\scripts\ai.ps1 issue "Titulo curto" --context "Sintoma e impacto"`
   - Nova capacidade: `.\scripts\ai.ps1 feature "Titulo curto" --context "Motivo e escopo"`
   - Ideia futura, sem prazo: `.\scripts\ai.ps1 backlog add "Ideia" --context "Quando pode ser util"`
2. **Implemente.** Edite arquivos. Se algum estiver travado em `features/registry.yaml`, siga [`docs/how-to/editar-arquivo-travado.md`](docs/how-to/editar-arquivo-travado.md).
3. **Marque pronto para validacao:**
   ```powershell
   .\scripts\ai.ps1 ready I-NNN `
       --file <caminho> [--file <outro>] `
       --summary "Resumo do que foi feito" `
       --validation "Comando ou check executado"
   ```
4. **Aguarde teste humano** (uso real, nao so test suite).
5. **Antes de fechar, rode o docs-check:**
   ```powershell
   .\scripts\ai.ps1 docs-check
   ```
   Le `.ai/docs-map.yaml` e lista docs vivos que podem precisar de atualizacao. Atualize o que fizer sentido. Sem mapa, vira no-op com aviso. Detalhes em [`docs/how-to/manter-docs-atualizados.md`](docs/how-to/manter-docs-atualizados.md).
6. **Feche:** `.\scripts\ai.ps1 finish I-NNN --docs-touched <path>...` ou `--docs-skip "<motivo>"`. Para travar arquivos homologados, use `--lock --lock-id <slug>`.

Detalhes de cada subcomando: [`docs/reference/cli.md`](docs/reference/cli.md).

## Editando skills

Skills sao geradas a partir de `skills/manifest.yaml` (fonte unica para Claude Code, Codex e Antigravity). Para alterar:

1. Edite `skills/manifest.yaml`.
2. Rode `python scripts/render-skills.py` para regenerar `skills/generated/`.
3. Em CI/hook, rode `python scripts/render-skills.py --check` para barrar drift.

**Nao edite arquivos sob `skills/generated/` a mao** - eles sao sobrescritos. Mais contexto em [`docs/how-to/instalar-em-outro-projeto.md`](docs/how-to/instalar-em-outro-projeto.md#editando-skills-geradas).

## Documentacao

Docs seguem [Diataxis](https://diataxis.fr/) - quatro pastas por intencao do leitor (`tutorials/`, `how-to/`, `reference/`, `explanation/`). Antes de criar arquivo novo, leia [`docs/explanation/por-que-diataxis.md`](docs/explanation/por-que-diataxis.md) para decidir a porta certa.

## Padrao de commit

Os commits desse repo seguem um prefixo curto que casa com o tipo de demanda:

```
<tipo>: <descricao no imperativo>
```

Tipos em uso:

| Tipo | Quando |
| --- | --- |
| `feature` | Nova capacidade entregue via `/feature`. |
| `issue` | Correcao ou regressao entregue via `/issue`. |
| `chore` | Manutencao sem demanda formal (libs, formatacao, build). |

Exemplos reais do historico:

```
feature: Diferenciar descriptions das skills para evitar trigger collision
issue: Paridade de skills/comandos entre Claude, Codex e Antigravity - usar fonte unica
chore: initial extraction from gerador-cortes (v0.1.0)
```

### Editando arquivos travados

Se a edicao toca arquivo travado em `features/registry.yaml`, a mensagem **precisa** conter:

```
[unlock:<feature-id>] motivo: <razao curta>
```

O hook `commit-msg` (instalado por `git config core.hooksPath .githooks`) rejeita commits sem essa marca. Receita completa: [`docs/how-to/editar-arquivo-travado.md`](docs/how-to/editar-arquivo-travado.md).

## Pull Requests

- Um PR por demanda (`F-NNN` ou `I-NNN`). Mantem revisao focada e rollback trivial.
- Inclua o ID da demanda no titulo do PR.
- Verifique antes de abrir:
  ```powershell
  .\scripts\ai.ps1 doctor
  python scripts/render-skills.py --check
  ```
  Ambos devem sair com codigo 0.
- Descreva o que foi feito e como testar em uso real (nao so test suite).
- Aceite que o `commit-msg` local pode rejeitar - **nao** use `--no-verify` para mascarar o erro. Se a trava parece errada, abra issue antes.

## Reportando

- **Bug ou comportamento errado:** abra issue no GitHub usando o template.
- **Falha de seguranca:** **nao** abra issue publica. Siga [`SECURITY.md`](SECURITY.md).
- **Conduta:** [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

## Licenca

Ao contribuir, voce concorda em licenciar sua contribuicao sob a [MIT](LICENSE), os mesmos termos do projeto.
