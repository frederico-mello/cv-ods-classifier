# Design

> Motivação e escopo: ver `proposal.md` (Why / What Changes). Este documento cobre **como**
> implementar — decisões técnicas, estrutura e limites de projeto. A fonte do escopo é
> `docs/12-plano-onda-m0.md`; requisitos comportamentais detalhados ficam com os specs
> (capacidades `cv-parsing`, `sdg-search`, `sdg-evidence`), gerados na fase seguinte.

## Context

Estado atual relevante para as decisões abaixo:

- `lattes_sdg/parser.py` (148 linhas): dict `TAG_TO_SECTION` com chaves **camelCase**
  (`tituloDoTrabalho`, `resumo`, `nomeDoEvento`...), `_text(node)` concatenando texto de
  filhos, `_walk()` recursivo, `parse_lattes_xml(xml_bytes) -> LattesDocument`.
  **Não lê atributos, não trata encoding.** Dataclasses `Field{section, text, weight=1.0}`
  (com `__post_init__` que normaliza espaços) e `LattesDocument{fields}` com
  `as_text()`, `by_section()`, `sections()`.
- CV real medido (fora deste clone): 41 tags MAIÚSCULAS com hífen, 154 atributos
  MAIÚSCULOS, ISO-8859-1 puro; `python demo.py cv-frederico.xml` → 0 campos, 17 notas
  zeradas (P0-1). Busca por substring: "Ciências" pontua ODS 9 (pista "ia"), "Maria"
  pontua ODS 14 (pista "mar") — P0-2.
- `lattes_sdg/scorer.py`: `Scorer(analyze)` monta `evidence` como `List[Dict[str, str]]`
  (chaves `keyword`/`section`), com `MAX_EVIDENCE_PER_SDG` e fallback por temas quando
  `not counts` — hoje roda por campo, não uma única vez por ODS. `lattes_sdg/sds.py`:
  `build_taxonomy()`.
- 9 testes em `tests/test_classifier.py`, verdes contra `exemplo_cv.xml` (formato
  camelCase **inventado** pelo projeto). Nenhum teste constrói ou compara `Field`
  diretamente (verificado por grep) — impacto do item C é baixo.
- Restrições de projeto que SHALL valer sempre: sem banco, sem rede, sem IA generativa;
  contrato público preservado (`parse_lattes_xml()` → `LattesDocument`; ferramentas do
  servidor MCP inalteradas); nenhuma dependência nova (stdlib: `unicodedata`, `re`,
  `xml.etree`).

Ver `proposal.md` — Why para a motivação completa; `docs/12-plano-onda-m0.md` §2–§5 para
o diagnóstico detalhado.

## Goals / Non-Goals

**Goals:**

- Ler a exportação oficial do Lattes (atributos MAIÚSCULOS, ISO-8859-1) mantendo
  `parse_lattes_xml()` como única porta de entrada e `LattesDocument` como única saída —
  Scorer e servidor SHALL não mudar de interface.
- Dados pessoais (PII) nunca viram `Field`: descarte no momento da extração, antes de
  qualquer mapeamento.
- Busca por pistas com normalização única (minúsculas + sem acento) nos dois lados,
  fronteira de palavra e ban-list com exceções explícitas — fim dos falsos positivos por
  substring.
- Evidências deduplicadas (máx. 1 por campo por ODS), fallback por temas uma única vez
  por ODS, e saída determinística: 2 execuções SHALL produzir JSON idêntico byte a byte
  (A6).
- Rastreabilidade: cada `Field` carrega `tag_origem`; cada evidência aponta o campo de
  onde veio.
- Base de teste ancorada no mundo real: 3 fixtures em `tests/fixtures/`, nenhuma com
  dados pessoais.

**Non-Goals:**

- Reconciliar números de decaimento/K dos docs 03/04 (Onda M1); D9 (origem de pistas na
  taxonomia) e D10 (modo ML).
- pyproject, LICENSE, CI, mensagens de erro amigáveis do servidor (Onda M2).
- Comparar currículos entre si (nunca foi o contrato — docs 04 e 07).
- Cobrir 100% das variantes históricas do Lattes na tabela de mapeamento: o desenho
  prevê crescimento da tabela sem mudança de arquitetura (premissa §8 do plano).
- Alterar assinaturas das ferramentas MCP, formato do JSON de saída além do campo
  adicional `tag_origem` (aditivo, ver D4) e a ordem/estrutura das notas.
- Gerar specs ou tasks neste artefato (fases seguintes do OpenSpec).

## Decisions

### D1 · Decodificação e leitura de tags + atributos (`cv-parsing`)

**Decisão:** um único ponto de decodificação na fronteira de `parse_lattes_xml()`, antes
do `ET.fromstring`. A codificação **declarada é ISO-8859-1** (realidade medida no CV real);
o **fallback UTF-8** é acionado por validação estrita dos bytes: se os bytes decodificam
como UTF-8 válido estrito e contêm sequências multibyte, usa-se UTF-8; caso contrário,
ISO-8859-1. Depois disso a varredura percorre **tags e atributos** de cada elemento
(localname sem namespace, como já faz `_localname`), casando contra a tabela (D2) em vez
de texto de elementos.

*Por que:* ISO-8859-1 nunca falha ao decodificar (mapeia os 256 bytes), então um
"fallback por exceção" nunca dispararia — a validação estrita UTF-8 é o gatilho
determinístico que distingue um arquivo latin-1 (bytes `0xE9` etc. são UTF-8 inválido) de
um já salvo em UTF-8. Um teste SHALL cobrir ambos os encodings (risco §9).

*Alternativas consideradas:* (a) confiar no `encoding` do XML declaration — rejeitado: o
export real é inconsistente nisso e o parser receberá `bytes` crus; (b) heurística de
"BOM/sniffing" por frequência de bytes — rejeitada: mais frágil que validação estrita;
(c) decodificar com `errors="replace"` — rejeitado: `�` corrompe pistas silenciosamente.

### D2 · Tabela explícita + rede de segurança por padrão (`cv-parsing`)

**Decisão:** duas camadas de tolerância, com ordem fixa de avaliação por atributo:

1. **Filtro PII (D3) primeiro** — negação tem precedência sobre qualquer mapeamento.
   Essa ordem é obrigatória: `NOME-DA-MAE` casa com o padrão da rede de segurança
   `NOME-DA-*`; sem a precedência do denylist, a mãe viraria campo.
2. **Tabela explícita** `elemento -> atributo -> seção -> peso` — via principal, uma
   linha por par. Trecho ilustrativo (a tabela completa vive no código):

   | Elemento | Atributo | Seção | Peso |
   |---|---|---|---|
   | `RESUMO-CV` | `TEXTO-RESUMO-CV-RH` | `resumo` | 0.8 |
   | `TRABALHO-EM-EVENTOS` → `DADOS-BASICOS-DO-TRABALHO` | `TITULO-DO-TRABALHO` | `pub_titulo` | 1.0 |
   | `TRABALHO-EM-EVENTOS` → `DETALHAMENTO-DO-TRABALHO` | `NOME-DO-EVENTO` | `pub_evento` | 0.5 |
   | `PROJETO-DE-PESQUISA` | `NOME-DO-PROJETO` | `projeto_titulo` | 0.8 |
   | `PALAVRA-CHAVE` | `PALAVRA-CHAVE-1..6` | `palavra_chave` | 0.7 |

   A tabela casará pelo par (elemento-pai, atributo) usando o caminho localname, não só a
   tag folha — `TITULO-DO-TRABALHO` só existe dentro de `DADOS-BASICOS-DO-TRABALHO`.
   Ela também **corrige P1-1**: `TITULO-DO-ARTIGO`/`TITULO-DO-TRABALHO`/`TITULO-DO-LIVRO`
   passam a pontuar em `pub_titulo`/`pub_obra` com peso 1.0.
3. **Rede de segurança por padrão de nome** *(premissa, aceitável para v1)* — atributos
   não mapeados cujo nome casa com `TITULO-*`, `NOME-DA-*`, `DESCRICAO-*` ou
   `*PALAVRA-CHAVE*` entram com peso conservador 0.5.
4. **Fora das três → IGNORADO.** Nenhum "catch-all" por texto longo ou por adivinhação.

*Regra especial:* atributos cujo nome termina em `-INGLES` (tradução automática do
Lattes) recebem o peso da linha correspondente **× 0.5**; o campo original (português)
pontua cheio. Evita inflar a nota pela mesma peça traduzida duas vezes (risco §9).

*Alternativas consideradas:* (a) só rede de segurança por padrão — rejeitada: não
distingue seção nem peso, alto risco de campo errado com peso alto; (b) só tabela
explícita — rejeitada: quebra silenciosamente com variação entre versões do export
(risco §9); (c) validar contra o XSD oficial do Lattes — rejeitada: dependência/complexidade
nova sem ganho (não precisamos de validação, precisamos de leitura tolerante).

### D3 · Filtro de PII no nascedouro (`cv-parsing`)

**Decisão:** denylist fixa de nomes de atributo avaliada **antes** de D2, descartando o
atributo sem nunca criar `Field`: `NOME-COMPLETO`, `NOME-EM-CITACOES-BIBLIOGRAFICAS`,
`CPF`, `NUMERO-IDENTIDADE`, `DATA-NASCIMENTO`, `TELEFONE`, `E-MAIL`, `LOGRADOURO`,
`BAIRRO`, `NOME-DO-PAI`, `NOME-DA-MAE`, `AUTORES`. Valores vazios ou só espaços também
não viram campo.

*Por que:* resolve P0-1 (nota movida pelo nome do pesquisador) e P0-2 parcialmente ao
mesmo tempo, e atende o requisito 5 do doc 07 numa camada só. `AUTORES` é incluído de
propósito: nomes de coautores são dados pessoais de terceiros e não são conteúdo acadêmico
para fins de ODS.

*Alternativas consideradas:* (a) filtrar no Scorer ou no servidor — rejeitado: a PII já
teria entrado em `LattesDocument`, ficaria em memória e em qualquer saída de depuração, e
o aceite A8 ficaria mais fraco; (b) allowlist de seções em vez de denylist — rejeitada:
denylist é mais simples de auditar e o "ignorar o resto" da camada 4 de D2 já é uma
allowlist de fato; (c) mascarar em vez de descartar — rejeitado: não gera valor e mantém
superfície de vazamento.

### D4 · `Field.tag_origem` e impacto (`cv-parsing` → `sdg-evidence`)

**Decisão:** acrescentar ao dataclass `Field` um quarto campo
`tag_origem: str = ""` (localname do elemento de origem), **depois** de `weight`, com
default. Análise de impacto (código atual verificado):

- **Construções existentes:** `Field(section=..., text=...)` (a única existente, em
  `parser.py:131`) e qualquer construção posicional `Field(s, t, w)` continuam válidas —
  o campo novo é o último e tem default. `__post_init__` (normalização de espaços em
  `text`) não muda.
- **Consumidores:** `LattesDocument.as_text()/by_section()/sections()` leem apenas
  `section`/`text`; `Scorer` filtra `f for f in doc.fields if f.text`. Nenhum itera
  atributos numerados nem depende do nº de campos do dataclass.
- **Testes:** grep mostra que nenhum teste constrói/compara `Field` diretamente — a
  igualdade/repr do dataclass ganha um 4º componente com default `""` dos dois lados,
  preservando a semântica atual.
- **Serialização:** hoje `Field` não é serializado (`asdict` não aparece no código); a
  saída pública são os `evidence: Dict[str, str]` montados no Scorer.

*Decisão correlata:* o Scorer copia `field_obj.tag_origem` para dentro da evidência
(chave aditiva `tag_origem`) — é o que concretiza "evidência rastreável até o XML"
(plano §3.4). A chave é **aditiva**: consumidores que leem `keyword`/`section` não quebram,
e o formato SHALL permanece `Dict[str, str]`.

*Alternativa considerada:* herdar de uma base comum ou usar um dict plano em vez de
dataclass — rejeitado: `LattesDocument` e `Scorer` já operam sobre dataclasses; um campo
com default é a mudança de menor difusão possível.

### D5 · Busca: normalização, fronteira e ban-list (`sdg-search`)

**Decisão:** três correções compostas num funil único, todas em `sds.py`/`scorer.py`:

1. **Mesma normalização nos dois lados:** função `normalizar()` única (minúsculas +
   remoção de acento via `unicodedata.normalize("NFD")` + descarte de marcas combinantes
   + colapso de espaços) aplicada ao texto dos campos **e** às pistas da taxonomia. A
   taxonomia é normalizada uma vez em `build_taxonomy()`; campos, na leitura.
2. **Fronteira de palavra:** a pista só casa se estiver cercada de não-alfanuvéricos
   (regex com lookarounds `(?<![0-9A-Za-z])pista(?![0-9A-Za-z])`, com espaços internos
   permitidos para expressões). Hífen conta como fronteira (o Lattes usa muito
   compostos), então "sustentabilidade-ambiental" ainda casa com "sustentabilidade".
   "mar" deixa de achar "Maria"; "ia" deixa de achar "Ciências".
3. **Ban-list com exceções:** pistas com **menos de 4 letras após normalização** não
   pontuam por padrão, salvo exceção explícita na taxonomia (flag por pista, ex.:
   `CO2` → normaliza para `co2`, 3 letras, mas é exceção e casa como palavra inteira).

A ban-list é defesa em profundidade: a fronteira de palavra já mata a substring, a
ban-list mata a palavra curta solta (ex.: "IA" num campo livre), que a fronteira não
impede.

*Alternativas consideradas:* (a) fronteira sem ban-list — rejeitada: palavras curtas
legítimas continuariam pontuando ruidosamente; (b) ban-list sem fronteira — rejeitada:
não resolve o P0-2 clássico (substring); (c) casar por token-inteiro (split em lista de
tokens) — rejeitado para expressões mult palavra e para pontuação inconsistente;
(d) subir o mínimo para letras sem exceção — rejeitado: mataria `CO2` sem caminho de
escape; (e) normalizar só o texto e comparar com pista crua — rejeitado: é exatamente o
funil assimétrico que hoje perde "climática" vs "climatica".

### D6 · Dedupe de evidências + fallback por temas (`sdg-evidence`)

**Decisão:**

- **Dedupe:** no máximo **1 evidência por (campo, ODS)**. Quando várias palavras-chave do
  mesmo ODS casam no mesmo campo, elas são **agrupadas na própria evidência** (lista de
  palavras) em vez de gerar entradas repetidas — restabelece o A5 e para de inflar a lista
  (P1-3).
- **Fallback:** a busca ampla por temas roda **uma vez por ODS**, somente quando
  **nenhuma** palavra-chave casou naquele ODS no currículo inteiro (`not counts` depois
  da varredura principal), e produz **no máximo 1 evidência por ODS** (seção
  `busca_ampla`) — restabelece o contrato do doc 04.
- **Determinismo (A6):** a iteração é sempre por ordem de inserção — ODS na ordem da
  taxonomia, campos na ordem do documento, palavras na ordem da taxonomia. **Nada de
  iteração sobre `set` de strings** para produzir saída (a ordem de hash de str varia com
  `PYTHONHASHSEED` entre processos); conjuntos servem só para membership, a saída vem de
  listas/dicts ordenados. 2 execuções ⇒ JSON idêntico byte a byte.

*Alternativas consideradas:* (a) dedupe por igualdade textual da evidência montada —
rejeitado: não agrupa palavras nem garante o máximo 1 por campo; (b) rodar o fallback e
depois cortar para 1 — rejeitado: desperdiça trabalho e torna a ordem de desempate
dependente da varredura; (c) ordenar a saída por nota (score desc) — rejeitado: empates
tornariam a ordem ambígua, a ordem de iteração estável é a garantia barata de A6.

### D7 · Fixtures como nova base de verdade (T1)

**Decisão:** três XMLs em `tests/fixtures/`, todos em formato oficial (tags MAIÚSCULAS,
atributos, ISO-8859-1 ou UTF-8 declarado):

| Fixture | Conteúdo | Uso |
|---|---|---|
| `cv_lattes_real_anon.xml` | CV real expurgado: nome→anônimo, CPF/telefones/endereços/e-mails/data de nascimento removidos; **títulos e seções mantidos** | leitura real (A1–A2, A8) |
| `cv_lattes_minimo.xml` | só nome + área, sem trabalhos | anti-falso-positivo (A3) |
| `cv_sintetico_formato_real.xml` | o atual `exemplo_cv.xml` reescrito no formato oficial | continuidade dos 9 testes (A7), demo |

**Regra de ouro:** nenhum teste depende de dados pessoais. O CV real original fica
**FORA do git** (entrará no `.gitignore` no T0); o expurgado passa por checklist de
expurgo e pelo teste A8, que varre **os campos extraídos** (CPF/e-mail/telefone), não o
arquivo. Os 9 testes atuais apontam para `cv_sintetico_formato_real.xml`, preservando
asserções e verificação A7.

*Alternativas consideradas:* (a) manter `exemplo_cv.xml` camelCase como fixture principal
— rejeitado: é o XML inventado que escondeu o P0-1; (b) gerar o fixture em tempo de teste
a partir do CV real — rejeitado: o CV real não pode estar no repositório; (c) fixture
real sem anonimização, só fora do git — rejeitado: qualquer cópia versionada é risco, o
expurgado é o artefato versionável.

### D8 · Onde cada mudança vive

| Módulo | Mudança |
|---|---|
| `lattes_sdg/parser.py` | reescrita: decodificação (D1), varredura de tags+atributos, tabela + rede (D2), denylist PII (D3), `Field.tag_origem` (D4) |
| `lattes_sdg/sds.py` | `normalizar()`, ban-list com exceções, pistas pré-normalizadas (D5) |
| `lattes_sdg/scorer.py` | casamento por fronteira (D5), dedupe + fallback por ODS (D6), chave `tag_origem` na evidência (D4) |
| `demo.py` | aponta para o fixture real expurgado |
| `tests/` | `tests/fixtures/` (3 XMLs), testes A1–A8, 9 testes re-apontados |

`server.py` **não muda** — o contrato das ferramentas MCP é preservado.

## Risks / Trade-offs

| Risco | Impacto | Mitigação |
|---|---|---|
| Tabela de mapeamento incompleta (variantes do Lattes) | campos perdidos, notas baixas demais | rede de segurança por padrão (peso 0.5) + a tabela cresce por linhas sem mudar o desenho; 2ª fixture real quando possível |
| Superajuste ao único CV real disponível | falsa sensação de pronto | fixture sintético em formato real + aceites por contagem/seção (A1: ≥30 campos, ≥5 seções), não por valores exatos de um CV |
| ISO-8859-1 × UTF-8 | texto corrompido, pistas perdidas | decode declarado + fallback por validação estrita (D1); teste com ambos os encodings |
| `TITULO-...-INGLES` duplicando pistas | nota inflada pela tradução | regra na tabela: original pontua cheio, `-INGLES` com peso × 0.5 (D2) |
| Fixture real mal anonimizada | vazamento de dados pessoais no git | checklist de expurgo + A8 varra os campos extraídos; CV real original fora do git (T0) |
| Rede de segurança cria campo com seção/peso imprecisos | nota levemente deslocada | peso conservador 0.5 fixo e aceito como premissa v1; tabela explícita sempre tem precedência |
| PII denylist derruba conteúdo acadêmico legítimo (ex.: `AUTORES`) | perda de recall | aceito: coautores não são conteúdo para ODS e são dados pessoais de terceiros (doc 07, req. 5) |
| Fronteira de palavra + ban-list reduzem recall de pistas curtas legítimas | alguns ODS deixam de pontuar | exceções explícitas na taxonomia (ex.: `CO2`); é o custo deliberado de matar P0-2 |
| Evidência ganha chave `tag_origem` (mudança aditiva no JSON de saída) | consumidores estritos de schema podem notar | chave aditiva, formato segue `Dict[str, str]`; nenhum código atual lê o JSON por posição |

Trade-off geral assumido: **precisão sobre cobertura** — é melhor ignorar um atributo
incerto (camada 4 de D2) do que inventar campo errado; o produto só é confiável quando a
nota explicável vem de conteúdo real.

## Migration Plan

Ordem de construção (plano §7), cada etapa verificável antes da seguinte:

1. **T0 · Higiene mínima** — criar `.gitignore` (inexistente), remover `__pycache__/` e
   `.pytest_cache/` versionados, tirar `cv-frederico.xml` da raiz do git (contém e-mail,
   data de nascimento, endereço). *Antes de tudo para que nenhum dado pessoal entre no
   histórico a partir daqui.*
2. **T1 · Fixtures** — os 3 XMLs de D7. *T1 antes de T2: sem fixture real, o parser novo
   seria validado contra o XML inventado de novo; o fixture é o quebra-cabeça que prova o
   parser.*
3. **T2 · Parser novo** — D1 + D2 + D3 + D4 (`parser.py`). *T2 antes de T3: a busca nova
   só faz sentido sobre campos reais — testada contra camelCase, esconderia o mesmo
   problema de sempre.*
4. **T3 · Busca nova** — D5 (`sds.py` + casamento no `scorer.py`).
5. **T4 · Dedupe + fallback** — D6 (`scorer.py`).
6. **T5 · Testes de aceite** — A1–A8 automatizados + os 9 testes atuais re-apontados (A7).
7. **T6 · Demo e docs (raso de propósito)** — `demo.py` aponta para o fixture real;
   sincronizar nos docs 03, 04 e 10 apenas os pontos que a onda mudou (seções novas,
   regra de evidência, fronteira de palavra). Reconciliação completa de números é da M1.

*Rollback:* o contrato público não muda (`parse_lattes_xml()` → `LattesDocument`), então
cada etapa é revertível por reversão do próprio módulo tocado, sem migração de dados (não
há banco) e sem consumidores externos a atualizar — o servidor MCP não é alterado.
*Cuidado esperado (BREAKING comportamental, já anunciado no proposal):* CVs que
pontuavam por substring/nome passam a devolver notas diferentes — CV mínimo → 17 zeros é
comportamento **desejado**, não regressão.

## Open Questions

- **Segunda fixture real (de outra pessoa, anonimizada).** Se existir, só acrescenta um
  arquivo de fixture — não muda specs, abordagem nem o desenho das tarefas; enquanto não
  chegar, a fixture sintética em formato real cobre os casos gerais (premissa §8 do plano).
- **Variante antiga de export (XML de integração, se alguma vez estiver em uso).** Se
  aparecer, cresce apenas a tabela de mapeamento (D2); o desenho — decodificação, denylist,
  rede de segurança, contrato `LattesDocument` — não muda (premissa §8).
