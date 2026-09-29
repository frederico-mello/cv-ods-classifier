# Proposal

> **Fonte do escopo:** `docs/12-plano-onda-m0.md` (plano de construção da Onda M0, derivado
> da auditoria de 25/09/2026). Este proposal resume esse plano; os artefatos seguintes
> (specs, design, tasks) derivam dele.

## Why

O sistema não lê o XML oficial do Lattes: `parser.py` procura texto em elementos
camelCase, mas o export real guarda os dados em **atributos** de tags MAIÚSCULAS com
hífen, em ISO-8859-1 — resultado medido: `python demo.py cv-frederico.xml` devolve
**0 campos e 17 notas zeradas** (P0-1). Em paralelo, a busca por pistas é substring, de
modo que "Ciências" pontua o ODS 9 pela pista "ia" e "Maria" pontua o ODS 14 pela pista
"mar" (P0-2): a nota atual é movida pelo **nome** do pesquisador, não pelo conteúdo.
A Onda M0 faz o produto atender o contrato que os docs 01–11 já prometem.

## What Changes

Escopo extraído de `docs/12-plano-onda-m0.md` (etapas T0–T6):

- **Novo parser para o XML oficial** (T2): decodificação ISO-8859-1 com fallback UTF-8,
  leitura de **atributos** de tags MAIÚSCULAS com hífen, **tabela de mapeamento
  explícita** (elemento → atributo → seção → peso) + rede de segurança por padrão de
  nome de atributo (`TITULO-*`, `NOME-DA-*`, `DESCRICAO-*`, `*PALAVRA-CHAVE*`) com peso
  conservador 0,5. `parse_lattes_xml()` continua devolvendo `LattesDocument` — contrato
  com Scorer e servidor **não muda**.
- **Filtro de dados pessoais dentro do parser**: CPF, e-mail, telefone, endereço,
  data de nascimento, nomes (própios e de terceiros/`AUTORES`) **nunca** viram campo.
  Resolve a nota movida por nomes e o requisito 5 do doc 07 ao mesmo tempo.
- **`Field` ganha `tag_origem`**: cada campo rastreia o elemento do XML de onde veio,
  mantendo a evidência rastreável até a origem.
- **Nova busca por pistas** (T3): normalização (minúsculas + sem acento) aplicada ao
  texto e às pistas pelo mesmo funil; **fronteira de palavra** (fim das substrings "ia",
  "mar"); **ban-list** para pistas com menos de 4 letras, com exceções explícitas na
  taxonomia (ex.: "CO2").
- **Fallback por temas restabelecido** (T4): a busca ampla por temas roda **uma vez por
  ODS**, somente quando nenhuma palavra-chave casou, e produz **no máximo 1 evidência
  por ODS** — conforme o doc 04.
- **Dedupe de evidências** (T4): um campo gera **no máximo 1 evidência por ODS**; as
  palavras-chave ficam listadas na própria evidência em vez de inflar a lista.
- **Correção do mapeamento de títulos de publicação**: `TITULO-DO-ARTIGO`,
  `TITULO-DO-TRABALHO`, `TITULO-DO-LIVRO` passam a pontuar em `pub_titulo`/`pub_obra`
  com peso 1,0 (hoje `tituloDoTrabalho` não está no mapa e pesos 1,0 são código morto).
- **Fixtures reais anonimizadas** (T1): `tests/fixtures/cv_lattes_real_anon.xml` (CV real
  expurgado), `cv_lattes_minimo.xml` (só nome+área) e
  `cv_sintetico_formato_real.xml` (o `exemplo_cv.xml` atual reescrito no formato
  oficial). Regra de ouro: nenhum teste depende de dados pessoais.
- **Higiene mínima** (T0): criar `.gitignore` (inexistente), remover `__pycache__` e
  `.pytest_cache` versionados e tirar `cv-frederico.xml` da raiz do git (contém e-mail,
  data de nascimento e endereço; o arquivo não é versionado, mas não pode passar a sê-lo).
- **Testes de aceite A1–A8** (T5) e **demo/docs** (T6): `demo.py` aponta para o fixture
  real; docs 03, 04 e 10 sincronizados nos pontos que a onda mudou (seções novas, regra
  de evidência, fronteira de palavra).

**BREAKING** (comportamental, não de API): CVs que antes pontuavam por substring/nome
passam a devolver notas diferentes — esperado e desejado (ex.: CV mínimo → 17 zeros;
hoje ODS 9 = 28,3 e ODS 14 = 19,3).

**Fora de escopo, de propósito** (Onda M1/M2, conforme plano §1): reconciliar números de
decaimento/K nos docs 03/04; D9 (origem de pistas) e D10 (modo ML); pyproject, LICENSE,
CI e mensagens de erro amigáveis; comparação entre currículos.

## Capabilities

> Inventário: `openspec list --specs` → **nenhum spec existente** (repositório novo no
> OpenSpec). Portanto **todas as capacidades abaixo são novas** e cada uma vira um
> `specs/<caminho>/spec.md`.

### New Capabilities

- `cv-parsing`: Leitura do XML oficial do Lattes — decodificação ISO-8859-1/UTF-8,
  extração a partir de **atributos** de tags MAIÚSCULAS com hífen via tabela de
  mapeamento explícita + rede de segurança por padrão de nome, descarte de dados
  pessoais (PII) no momento da extração, anotação de origem (`tag_origem`) em cada
  campo e devolução do `LattesDocument` pela API atual.
- `sdg-search`: Busca por pistas dos ODS — normalização de acento/minúsculas em texto e
  pistas, comparação por **fronteira de palavra**, ban-list de pistas com menos de 4
  letras com exceções explícitas na taxonomia e fallback por temas que roda uma única
  vez por ODS, somente quando nenhuma palavra-chave casou.
- `sdg-evidence`: Evidências que explicam a nota — no máximo **1 evidência por campo por
  ODS**, agrupamento das palavras-chave na própria evidência, fallback limitado a 1
  evidência por ODS e determinismo byte a byte da saída.

### Modified Capabilities

*(vazio — nenhum spec existente foi modificado.)*

## Impact

- **Código:** `lattes_sdg/parser.py` (reescrita — hoje 148 linhas com o dict
  `TAG_TO_SECTION` em camelCase lendo texto de elementos), `lattes_sdg/scorer.py`
  (dedupe de evidências + fallback por tema), `lattes_sdg/sds.py` (normalização, ban-list
  e exceções), `demo.py` (aponta para o fixture real). Contrato público
  (`parse_lattes_xml()` → `LattesDocument`; ferramentas do servidor MCP) **preservado**.
- **Testes:** `tests/test_classifier.py` (9 testes atuais devem continuar verdes — A7,
  apontados para `cv_sintetico_formato_real.xml`) + novos testes A1–A8. Novo diretório
  `tests/fixtures/` com 3 XMLs.
- **Repositório:** novo `.gitignore`; remoção de `__pycache__/` e `.pytest_cache/` do
  versionamento; `cv-frederico.xml` sai da raiz do git (dado pessoal: e-mail,
  data de nascimento, endereço). Nenhum arquivo binário ou dado pessoal entra.
- **Docs:** `docs/03-modelo-de-dados.md`, `docs/04-algoritmo.md` e
  `docs/10-estrutura.md` atualizados nos pontos tocados (T6) — reconciliação completa de
  números fica para a M1.
- **Dependências/infra:** nenhuma nova — sem banco, sem rede, sem IA generativa (as três
  garantias de projeto seguem de pé).
- **Estado atual (baseline):** docs 01–12 commitados, 9 testes pytest verdes, demo
  funcional; **nenhuma etapa T0–T6 foi executada** — a Onda M0 está apenas planejada.
