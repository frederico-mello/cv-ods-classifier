# Pacote de Arquitetura — Classificador de Currículo Lattes por ODS

> Documento de arquitetura do sistema **Lattes‑SDG**: um servidor MCP que analisa um
> Currículo Lattes e classifica o quanto ele atende a cada um dos **17 ODS da ONU**.

Este pacote é o **entregável de arquitetura**. O código em `lattes_sdg/` é um
rascunho de referência (a implementação vive na raiz do projeto, fora deste `docs/`).

---

## Como navegar neste pacote

| Nº | Documento | Para quem é | O que responde |
|----|-----------|-------------|----------------|
| 01 | [A ideia, sem TI](01-conceito.md) | Qualquer pessoa | "O que isso é e por que existe?" |
| 02 | [Arquitetura](02-arquitetura.md) | Quem quer a visão geral | "Como as peças se encaixam?" |
| 03 | [Modelo de domínio](03-modelo-de-dados.md) | Quem quer entender os conceitos | "Quais são as coisas e suas regras?" |
| 04 | [Algoritmo de classificação](04-algoritmo.md) | Quem quer saber "como chega no número" | "De onde vem a nota de cada ODS?" |
| 05 | [Interface MCP](05-interface.md) | Quem conecta um cliente | "Quais ferramentas existem e como usá‑las?" |
| 06 | [Runtime e implantação](06-runtime.md) | Quem vai rodar | "Como executa e se conecta?" |
| 07 | [Requisitos não‑funcionais](07-nf.md) | Quem cuida da qualidade | "Determinismo, segurança, performance?" |
| 08 | [Decisões de arquitetura](08-decisions.md) | Quem avalia opções | "Por que cada escolha foi feita?" |
| 09 | [Glossário](09-glossario.md) | Não‑TI | "O que significa ODS, MCP, XML, score?" |
| 10 | [Visão do código](10-estrutura.md) | Quem vai mexer na implementação | "Onde cada coisa vive no repo?" |

> **Regra deste pacote:** cada documento é independente. Você pode abrir qualquer um
> e entender o assunto dele sem ler os outros — mas eles formam uma história única.

---

## A história, em uma frase

Você aponta um currículo Lattes (arquivo XML oficial) para o sistema, e ele responde:

> *"seu currículo contribui bastante para o ODS 13 (Ação Climática) e ODS 15 (Vida
> Terrestre), moderadamente para ODS 4 (Educação) e ODS 9 (Inovação), e praticamente
> não menciona ODS 14 (Vida na Água)."*

Os próximos documentos explicam como esse sistema é projetado para fazer isso — e por quê.
