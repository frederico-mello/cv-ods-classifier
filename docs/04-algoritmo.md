# 04 · O Algoritmo de Classificação

> Como o sistema chega na nota de 0 a 100 para cada ODS — sem magia, sem IA adivinhando.

Este é o coração do sistema. Ele responde à pergunta: *"por que o ODS 13 tem 75 e não 90?"*

Se você quer entender o **que** o sistema guarda, leia [03 — Modelo de Dados](03-modelo-de-dados.md).
Aqui vamos ao **como** ele pontua.

---

## 1. A ideia central: "caçar pistas"

O algoritmo funciona como um detetive que passa uma lista de ODS na mão de cada
documento, procurando **pistas**. Uma pista é quando **uma palavra de um ODS aparece num
campo do currículo**.

```mermaid
flowchart TB
    A["Para cada ODS"] --> B["Passa em todos<br/>os campos do<br/>currículo"]
    B --> C{"Palavra-chave<br/>do ODS apareceu?"}
    C -->|Sim| D["Anota uma<br/>pista"]
    C -->|Não| E["Próximo<br/>campo"]
    E --> B
    D --> F["Some as pistas<br/>com pesos"]
```

> **Analogia:** é como passar um ímã em cima de um monte de areia. As pistas são os
> preguinhos que o ímã (o ODS) consegue puxar. Quanto mais preguinhos, maior a nota.

### O funil: quando duas strings são a mesma palavra

Antes de comparar, texto e pista passam pelo **mesmo funil** — é ele que decide o que
conta como palavra:

```mermaid
flowchart LR
    A["texto do campo<br/>+ pista do ODS"] --> B["1. Normaliza<br/>minúsculas, sem acento"]
    B --> C["2. Compara com<br/>fronteira de palavra"]
    C --> D{"pista tem<br/>menos de 4 letras?"}
    D -->|"sim, sem exceção<br/>(ban-list)"| Z["não pontua"]
    D -->|"não, ou é exceção<br/>(ex.: CO2)"| P["pista válida"]
```

1. **Normalização única** — minúsculas, sem acento, espaços colapsados, aplicada dos
   dois lados: `climática` e `climatica` viram a mesma coisa.
2. **Fronteira de palavra** — a pista só casa cercada de limites de palavra: `ia` não
   casa em "Ciências" (o pedaço está no meio da palavra) e `mar` não casa em "Maria".
   Hífen conta como fronteira (`pesquisa-e-desenvolvimento` é dividido em palavras).
3. **Ban-list com exceções** — pista com menos de 4 letras não pontua por padrão; a
   taxonomia autoriza pontualmente (ex.: `CO2`).

> **Por que isso importa?** Antes, a comparação era por substring: a nota era movida por
> **nomes** ("Maria" pontuava o ODS 14 pela pista "mar"). Com o funil, só o conteúdo
> acadêmico pontua — e dados pessoais nem chegam ao algoritmo, porque o parser os
> descarta antes (ver [03 — Modelo de Dados](03-modelo-de-dados.md)).

---

## 2. Os quatro passos da nota

O cálculo da nota é feito em **quatro etapas**, sempre na mesma ordem:

```mermaid
flowchart LR
    P1["1. Pesar<br/>(peso da seção)"] --> P2["2. Somar<br/>(com decaimento)"]
    P2 --> P3["3. Saturar<br/>(curva de 0..100)"]
    P3 --> P4["4. Explicar<br/>(listar pistas)"]
```

### Passo 1 — Pesar
Cada pista ganha o **peso da seção** onde apareceu. Uma publicação sobre clima vale mais
que uma menção solta:

| Onde a pista apareceu | Peso |
|-----------------------|------|
| Linha de pesquisa / título de publicação | 1.0 |
| Título de projeto | 0.8 |
| Resumo / descrição | 0.7 |
| Formação | 0.4 |
| Menção genérica | 0.3 |

### Passo 2 — Somar (com decaimento)
Se a mesma pista aparece várias vezes, a **1ª** conta 100%, a **2ª** conta 70%, a **3ª**
50% etc. Isso evita que um ODS ganhe nota alta só porque a palavra se repetiu.

> **Por que isso importa?** Um currículo que repete "clima" 50 vezes não deveria
> automaticamente bater um que fala de clima 500 vezes. A soma "decai", ficando mais
> lenta a cada ocorrência — como um copo que enche rápido no começo e devagar no fim.

### Passo 3 — Saturar (a curva)
A soma bruta é convertida em nota de 0 a 100 por uma **curva exponencial**:

```
nota = 100 × (1 − e^(−soma ÷ K))
```

onde **K** é um número que controla a "velocidade" da curva (no rascunho, K = 2,3 — valor recalibrado na v2; ver o exemplo da seção 4).

> **Os números exatos vivem no código:** decaimento (`DECAY`), constante `K`
> (`SATURATION_K`) e pesos de seção (`SECTION_WEIGHTS`) estão em
> `lattes_sdg/scorer.py`. A reconciliação deste documento com esses valores é da
> Onda M1 — a Onda M0 mudou a leitura e a busca, não o cálculo.

```mermaid
xyChart
    title "Soma bruta → Nota (0 a 100)"
    xaxis "Soma bruta" [0, 2, 4, 6, 8, 10]
    yaxis "Nota" [0, 25, 50, 75, 100]
    line [0, 17, 33, 46, 56, 64]
    line [0, 33, 51, 65, 75, 82]
```

> **Ler o gráfico:** notas sobem rápido no começo e desaceleram no fim. Isso significa
> que **poucas pistas já dão uma nota razoável**, mas chegar perto de 100 exige
> **muitas pistas** — e não vale a pena repetir palavras infinitamente.

### Passo 4 — Explicar
O sistema lista as **pistas** que formaram a nota (limitado a 6 por ODS). Assim, a nota
nunca é um número misterioso — ela sempre tem **evidências** que a justificam.

A lista é deduplicada antes de sair:

| Regra | Efeito |
|-------|--------|
| **1 evidência por campo por ODS** | várias palavras do mesmo ODS no mesmo campo viram **uma** evidência agrupada (`keyword`), não três |
| **campos distintos → evidências distintas** | rastreabilidade preservada; nenhuma combinação campo/ODS aparece duas vezes |
| **máx. 6 evidências por ODS** | o resto é cortado — a nota continua contando tudo, só a explicação encurta |
| **fallback máx. 1 evidência por ODS** | a busca ampla entra como uma evidência só, na seção `busca_ampla` |

Cada evidência carrega `section`, `tag_origem` (a tag do XML de onde o campo veio) e
`text` (o trecho citado, truncado em 120 caracteres) — dá para voltar do resultado até a
origem no arquivo.

---

## 3. O que conta como "pista"

O ODS tem **duas rodadas** de busca — e a segunda só existe se a primeira falhar:

| Rodada | Como funciona | Quando |
|--------|---------------|--------|
| **Varredura principal** | para cada campo, procura palavras‑chave **e** temas com o funil (normalização + fronteira + ban‑list) | sempre |
| **Fallback por temas** | uma única passagem por **todo o texto** do currículo, por ODS | **só** se a varredura principal não achou nada; emite **no máximo 1 evidência** |

```mermaid
flowchart TB
    A["Varredura principal<br/>(campo a campo)"] --> B{"alguma pista<br/>casou neste ODS?"}
    B -->|sim| C["conta com peso e decaimento<br/>1 evidência por campo"]
    B -->|não| D["Fallback por temas<br/>1 vez por ODS"]
    D --> E{"tema casou no<br/>texto inteiro?"}
    E -->|sim| F["pista de tema<br/>(máx. 1 evidência)"]
    E -->|não| Z["ODS fica zerado"]
```

> **Por que duas rodadas?** As palavras‑chave são precisas; os temas são amplos e podem
> se partir entre campos (uma expressão começa em um campo e termina em outro). O fallback
> cobre esse caso **uma vez só** — sem inflar a lista de evidências nem rodar por campo.

> **Só conteúdo pontua:** a busca vê o texto dos campos; CPF, e‑mail, telefone e nomes
> nunca chegam aqui, porque o parser os descarta antes (requisito 5 do
> [07 — Não Funcionais](07-nf.md)).

---

## 4. Exemplo prático: ODS 13 em um currículo

Considere um currículo com:

- **Linha de pesquisa:** *"Mudanças Climáticas e Ecossistemas"*
- **Publicação:** *"Aquecimento Global e Biodiversidade Florestal"*
- **Palavras‑chave:** *"mudanças climáticas"*

Para o **ODS 13 (Ação Climática)**, o Scorer encontra:

| Pista | Seção | Peso |
|-------|-------|------|
| clima | linha de pesquisa | 1.0 |
| clima | publicação | 1.0 |
| clima | palavra‑chave | 0.7 |

Soma bruta ≈ 1,0 + 1,0×0,7 + 0,7×0,7² ≈ **2,35**

Aplicando a curva: `100 × (1 − e^(−2,35/1,4))` ≈ **64** (nota)

> O resultado final mostra: *"ODS 13: 64 — pistas encontradas: clima (linha, publicação, palavra‑chave)"*.

---

## 5. O que o algoritmo NÃO faz (e por quê)

| O que NÃO faz | Por quê |
|---------------|---------|
| **Usar IA generativa** | Daria respostas inconsistentes; o Lattes exige determinismo |
| **Adivinhar o contexto** | "água" pode ser ODS 6 ou 14; ele não "sabe", ele "pega pistas" |
| **Normalizar entre currículos** | Não compara dois currículos; cada um é analisado sozinho |

> **Isso é de propósito:** para análise acadêmica, é melhor **verificável** do que
> "inteligente". Um avaliador precisa poder **reproduzir** a nota, passo a passo.

---

## 6. Do XML decodificado à serialização

O algoritmo não começa no "caçar pistas": antes dele, o arquivo precisa virar campo.
Este é o percurso completo, do arquivo ao JSON:

```mermaid
flowchart LR
    X["arquivo .xml<br/>(bytes)"] --> D["1 · Decodifica<br/>ISO-8859-1<br/>(fallback UTF-8)"]
    D --> P["2 · Varre tags<br/>e atributos"]
    P --> F["3 · Filtro PII<br/>+ tabela de<br/>mapeamento"]
    F --> L["LattesDocument<br/>(campos)"]
    L --> S["4 · Busca na<br/>taxonomia<br/>(funil)"]
    S --> C["5 · Pesa + decai<br/>+ satura"]
    C --> A["CVAnalysis<br/>(17 notas)"]
    A --> J["6a · JSON<br/>(servidor MCP)"]
    A --> M["6b · texto<br/>(demo.py)"]
```

| Etapa | Módulo | Entrada | Saída |
|-------|--------|---------|-------|
| 1 · Decodificação | `parser.py` | bytes do arquivo | texto (`str`) |
| 2 · Varredura | `parser.py` | árvore de elementos | atributos por tag |
| 3 · Mapeamento + filtro | `parser.py` | atributos | `Field{secao, texto, peso, tag_origem}` |
| 4 · Busca | `sds.py` + `scorer.py` | campos × pistas | correspondências por ODS |
| 5 · Nota | `scorer.py` | pesos das ocorrências | `SDGScore{score, evidence}` |
| 6 · Serialização | `server.py` / `demo.py` | `CVAnalysis` | JSON (UTF‑8, `ensure_ascii=False`) ou texto impresso |

> **Contrato preservado:** a porta de entrada continua `parse_lattes_xml(bytes) →
> LattesDocument`. Scorer e servidor não sabem que o leitor por baixo mudou — e a saída é
> determinística: mesma entrada, mesmo JSON byte a byte (critério A6).

---

## 7. Resumo

O algoritmo é uma linha de montagem:

1. **Decodifica e converte** o XML oficial em campos (sem dados pessoais)
2. **Cace pistas** (palavras‑chave sempre; temas em fallback, uma vez por ODS)
3. **Pese** cada pista pelo peso da seção
4. **Some** com decaimento (repetição vale menos)
5. **Sature** numa curva de 0 a 100
6. **Explique** listando as pistas — uma por campo, com seção, `tag_origem` e trecho

Mesma entrada → mesma saída, sempre. E cada nota vem com suas pistas — nenhuma é mágica.
