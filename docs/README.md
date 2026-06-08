# Documentacao

Organizada segundo o framework [Diataxis](https://diataxis.fr/): cada documento serve a uma intencao especifica.

| Quadrante | Quando ler |
| --- | --- |
| [Tutorials](tutorials/) | Voce e novo. Quer ser levado do zero a um resultado funcionando. |
| [How-to](how-to/) | Voce ja entende o basico. Tem um problema concreto: "como faco X?". |
| [Reference](reference/) | Voce sabe o que quer. Precisa da sintaxe exata, lista completa, schema. |
| [Explanation](explanation/) | Voce quer entender por que o sistema e como e. Decisoes, tradeoffs, conceitos. |

Esta separacao nao se confunde com [`../README.md`](../README.md) (porta de entrada do projeto) nem com [`../CHANGELOG.md`](../CHANGELOG.md) (historico de versoes). Diataxis governa apenas o conteudo desta pasta.

## Tutorials

- [Primeiro uso](tutorials/primeiro-uso.md) - do clone ate finalizar a primeira demanda.

## How-to

- [Instalar em outro projeto](how-to/instalar-em-outro-projeto.md)
- [Configurar hooks git](how-to/configurar-hooks-git.md)
- [Promover item do backlog](how-to/promover-backlog.md)
- [Renomear o chat](how-to/renomear-chat.md)
- [Travar um arquivo](how-to/travar-arquivo.md)
- [Editar arquivo travado](how-to/editar-arquivo-travado.md)
- [Destravar arquivo permanentemente](how-to/destravar-arquivo.md)
- [Renomear arquivo travado](how-to/renomear-arquivo-travado.md)
- [Auditar desbloqueios](how-to/auditar-desbloqueios.md)

## Reference

- [CLI (`guia.py` / `guia.ps1`)](reference/cli.md) - todos os subcomandos e flags.
- [Arquivos do processo](reference/files.md) - layout de `.guia/`, `FEATURES.md`, skills.
- [Schema do `registry.yaml`](reference/registry-yaml.md) - locks, operacoes, lock-ignore.
- [Hooks git](reference/hooks-git.md) - hooks disponiveis, bypass, dependencias.
- [Renomear chat por ferramenta](reference/chat-rename-suporte.md) - Codex, Claude, Antigravity.
- [Troubleshooting](reference/troubleshooting.md) - erros comuns.

## Explanation

- [Visao geral do processo](explanation/visao-geral.md) - skill, script, JSON, YAML, hooks.
- [Por que o script e fonte da verdade](explanation/por-que-script-fonte-da-verdade.md)
- [Por que travar arquivos](explanation/por-que-lock.md) - tres camadas de defesa.
- [Convencoes de lock](explanation/convencoes-de-lock.md) - granularidade, nomes, quando travar.
- [Por que Diataxis](explanation/por-que-diataxis.md) - motivacao desta reestruturacao.

## Outros documentos nesta pasta

- [`ROADMAP.md`](ROADMAP.md) - planejamento de versoes. Nao e Diataxis (e planejamento de projeto, nao documentacao de uso).
- [`adr/`](adr/) - Architecture Decision Records. Registros curtos das decisoes arquiteturais (Contexto / Decisao / Consequencias). Nao e Diataxis (e historico de decisoes, nao documentacao de uso).
