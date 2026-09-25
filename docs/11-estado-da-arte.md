# 11 · Estado da Arte e Taxonomias Abertas

> O que já existe no mundo para "mapear pesquisa em ODS" — e como o Lattes‑SDG se apoia nisso.

Este documento nasceu de uma **pesquisa de estado da arte** (setembro de 2026), feita antes
desta revisão v2. Ele responde: *antes de inventar, quem já fez isso e o que dá para aproveitar?*

---

## 1. O que a pesquisa encontrou

Mapear produção científica em ODS **não é território novo** — é um campo consolidado, com
iniciativas abertas que já construíram as "réguas". Três se destacam:

| Iniciativa | Quem mantém | O que oferece de aberto | Como o Lattes‑SDG usa |
|------------|-------------|--------------------------|------------------------|
| **SDSN SDG Keyword List** | Rede de Soluções Sustentáveis da ONU | A primeira lista de palavras‑chave por ODS | Semente das palavras‑chave da taxonomia |
| **Elsevier SDG Research Mapping** | Editora Elsevier | Queries por ODS + dataset e componente de ML abertos (versões 2021 e 2023) | Semente das pistas + referência para o modo ML |
| **Aurora SDG Classification** | Rede de universidades europeias | Classificador open‑source e datasets públicos (Zenodo) | Semente + fundamento do caminho híbrido |

Universidades (ex.: Universidade do Sul da Dinamarca, University of Auckland) já compararam
essas listas entre si — ou seja, **as diferenças entre as "réguas" foram estudadas**, e as
listas podem ser combinadas com ciência.

**Fontes principais:**
- Elsevier — SDG Research Mapping Initiative: https://www.elsevier.com/about/sustainability/sdg-research-mapping-initiative
- Aurora (dataset de pesquisa): https://zenodo.org/records/3813230

---

## 2. O que a pesquisa NÃO encontrou

- **Nenhum servidor MCP pronto** que faça "Lattes → ODS": nem no registro oficial de
  servidores MCP, nem em buscas amplas. O nicho segue aberto — o Lattes‑SDG não está
  reinventando a roda do mapeamento, está levando a roda a um formato novo.
- Nada específico para o **XML do Lattes**: as taxonomias existentes foram feitas para
  títulos e resumos em inglês. A tradução e a adaptação ao vocabulário do Lattes são
  trabalho próprio deste projeto.

---

## 3. Como isso mudou a arquitetura (v2)

1. **D9 (novidade):** as pistas da SDGTaxonomy são **semeadas** das listas SDSN/Elsevier/Aurora,
   traduzidas ao português, adaptadas ao vocabulário do Lattes e anotadas com a **origem**
   de cada palavra.
2. **D10 (novidade):** o classificador da Aurora e o componente de ML da Elsevier fundamentam
   um **modo ML opcional**, sempre ao lado (nunca no lugar) da base determinística.
3. **Comparabilidade:** partindo das mesmas listas, as notas do Lattes‑SDG podem ser discutidas
   junto com classificações internacionais — a mesma régua, dois contextos.

---

## 4. Limites desta pesquisa (honestidade)

- Foi uma **busca direcionada** (consultas rápidas), não uma revisão sistemática da literatura.
- As listas da SDSN e da Elsevier **mudam com o tempo**; o projeto referencia versões, e a
  taxonomia do Lattes‑SDG deve registrar qual versão semeou cada palavra.
- Tradução e adaptação são etapas **revisáveis por humano** — tradução automática malfeita
  degradaria a precisão das pistas.