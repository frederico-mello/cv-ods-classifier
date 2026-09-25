# Classificador de Currículo Lattes por ODS da ONU

Um **servidor MCP (Model Context Protocol)** que lê um Currículo Lattes (arquivo XML oficial),
analisa o conteúdo e classifica **o quanto esse currículo atende a cada um dos 17 ODS (Objetivos de
Desenvimento Sustentável) da ONU**.

---

## 📖 Pacote de Arquitetura (leia isto primeiro)

O **entregável de arquitetura** é um pacote de documentos em [`docs/`](docs/), no mesmo espírito
de explicações para não‑TI. Abra o [`docs/README.md`](docs/README.md) para navegar.

| Nº | Documento | Para quem é |
|----|-----------|-------------|
| 01 | [A ideia, sem TI](docs/01-conceito.md) | Qualquer pessoa |
| 02 | [Arquitetura](docs/02-arquitetura.md) | Visão geral |
| 03 | [Modelo de dados](docs/03-modelo-de-dados.md) | Os conceitos |
| 04 | [Algoritmo](docs/04-algoritmo.md) | Como a nota é calculada |
| 05 | [Interface](docs/05-interface.md) | Como usar as ferramentas |
| 06 | [Runtime](docs/06-runtime.md) | Como rodar |
| 07 | [Requisitos não-funcionais](docs/07-nf.md) | Qualidade |
| 08 | [Decisões](docs/08-decisions.md) | Por que cada escolha |
| 09 | [Glossário](docs/09-glossario.md) | Palavras técnicas |
| 10 | [Estrutura do código](docs/10-estrutura.md) | Para quem vai codar |

---

## O que o sistema faz

Você aponta um currículo Lattes (arquivo XML oficial) para o sistema, e ele responde:

> *"seu currículo contribui bastante para o ODS 13 (Ação Climática) e ODS 15 (Vida<br/>
> Terrestre), moderadamente para ODS 4 (Educação) e ODS 9 (Inovação), e praticamente<br/>
> não menciona ODS 14 (Vida na Água)."*

---

## Arquitetura (resumo)

O sistema é dividido em **quatro camadas**, cada uma com uma única responsabilidade:

```mermaid
flowchart TB
    subgraph MCP["Servidor MCP (lattes_sdg/)"]
        DIR["Conexção (stdio)"]
        DIR --> P["1 · LattesParser<br/>XML Lattes → campos"]
        P --> S["3 · Scorer<br/>campos → nota 0–100"]
        S --> R["4 · ReportBuilder<br/>nota → JSON"]
        S --> TAX["2 · SDGTaxonomy<br/>17 ODS + pistas"]
    end
    CLIENTE -.-> "arquivo .xml" .-> P
```

| # | Camada | Arquivo | Função |
|---|--------|---------|--------|
| 1 | LattesParser | `lattes_sdg/parser.py` | XML Lattes → campos categorizados |
| 2 | SDGTaxonomy | `lattes_sdg/sds.py` | Define os 17 ODS e as pistas |
| 3 | Scorer | `lattes_sdg/scorer.py` | Calcula a nota de 0 a 100 |
| 4 | ReportBuilder | `lattes_sdg/server.py` | Expõe as ferramentas MCP |

**Método:** correspondência dirigida por conhecimento (palavras‑chave + pesos), **não IA
generativa** → resultado determinístico, reproduzível e auditável.

---

## Ferramentas expostas

| Ferramenta | O que faz |
|------------|-----------|
| `analyze_cv` | Analisa um currículo e nota os 17 ODS + ranking + top 5 |
| `get_sdg_report` | Relatório estruturado com scores, ODS top e pistas |

Entrada aceita: **XML colado** ou **caminho de arquivo** (`.xml`).

---

## Como rodar

```bash
python -m lattes_sdg.server   # inicia o servidor MCP (stdio)
python demo.py                # roda a análise no exemplo_cv.xml
python tests/test_classifier.py  # roda os testes
```

Configuração de um cliente MCP:

```json
{
  "mcpServers": {
    "lattes-sdg": {
      "command": "python",
      "args": ["-m", "lattes_sdg.server"]
    }
  }
}
```

---

## Estrutura do projeto

```
cv-ods-classifier/
├── docs/                    # Pacote de arquitetura (leia isto)
├── lattes_sdg/              # Implementação (rascunho de referência)
│   ├── parser.py            #   camada 1
│   ├── sds.py               #   camada 2
│   ├── scorer.py            #   camada 3
│   └── server.py            #   camada 4
├── tests/
│   └── test_classifier.py   #   9 testes
├── demo.py                  # roda sem cliente
├── exemplo_cv.xml           #   currículo de exemplo
└── requirements.txt
```

---

## Status

- ✅ Implementação funcionando
- ✅ 9/9 testes passando
- ✅ Pacote de arquitetura completo em `docs/`
