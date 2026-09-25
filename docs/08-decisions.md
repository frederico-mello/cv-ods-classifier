# 08 · Decisões de Arquitetura

> As escolhas que fizemos **por quê** — e as opções que **descartamos**.

Um documento de arquitetura bom não diz só "assim é". Ele mostra **por que** foi assim,
quais caminhos alternativos existiam e por que não foram escolhidos. Este documento é a
"prova" de cada decisão.

---

## D1 · Servidor MCP em vez de um script qualquer

**Por que servidor?** O pedido era explícito: *"um servidor MCP."* Mas vale entender o
ganho.

| Opção | Vantagem | Desvantagem |
|-------|----------|-------------|
| **Script Python** | Simples, direto | Isolado, não "fala" com IAs |
| **API web (REST)** | Acessível por rede | Precisa de servidor, porta, internet |
| **Servidor MCP (escolhida)** | Fala com IAs (goose, Claude) via padrão universal | Um pouco mais de estrutura |

**Decisão:** servidor MCP. O sistema foi concebido para ser **usado por uma IA** (o goose,
por exemplo), não por um humano digitando no navegador. O MCP é o **protocolo universal**
que permite isso — e o padrão local (stdio) evita abrir portas na rede.

---

## D2 · Correspondência por conhecimento em vez de IA generativa

**Por que não só deixar a IA ler o currículo?** Porque IAs generativas são **inconsistentes**:
a mesma nota pode mudar de uma chamada para outra. Para currículos acadêmicos, isso é
inaceitável.

| Opção | Vantagem | Desvantagem |
|-------|----------|-------------|
| **IA generativa** | "Entende" contexto | Resultado muda a cada chamada |
| **Aprendizado de máquina** | Aprende padrões | Precisa de muitos exemplos rotulados |
| **Correspondência por conhecimento (escolhida)** | Determinístico, explicável, auditável | Menos "inteligente" |

**Decisão:** correspondência por conhecimento. O sistema é **guiado por regras** (palavras‑chave
+ pesos), não por IA. O preço é ser menos "inteligente"; o ganho é ser **reproduzível e
explicável** — o que importa mais para análise acadêmica.

---

## D3 · Quatro camadas em vez de um módulo só

**Por que dividir?** Um único arquivo faria tudo junto: leitura, ODS, pontuação e resposta.
Fácil de escrever, difícil de manter.

| Opção | Vantagem | Desvantagem |
|-------|----------|-------------|
| **Um módulo só** | Simples | Mudança numa parte mexe em tudo |
| **Quatro camadas (escolhida)** | Mudança localizada, testável isoladamente | Um pouco mais de organização |

**Decisão:** quatro camadas, cada uma com **uma responsabilidade**. Assim, mudar um ODS
não quebra a análise; mudar a saída não quebra a pontuação. É o clássico trade‑off:
mais organização agora, menos dor de cabeça depois.

---

## D4 · Nota de 0 a 100 com curva de saturação

**Por que não somar pistas direto?** Se cada pista valesse 1 ponto, um currículo que
repete "clima" 100 vezes teria nota 1000. Precisaríamos de um teto arbitrário.

| Opção | Vantagem | Desvantagem |
|-------|----------|-------------|
| **Soma linear** | Simples | Repetições inflam a nota |
| **Soma + decaimento (escolhida)** | Repetições valem menos | Um pouco mais de matemática |
| **Curva de saturação** | Escala natural 0–100 | Precisa de uma constante K |

**Decisão:** soma com **decaimento** (repetição vale menos) + **curva de saturação**
(exponencial). Isso dá notas de 0 a 100 que sobem rápido no começo e desaceleram no fim
— o que faz sentido: poucas pistas já dão nota razoável, mas chegar no topo exige muito.

---

## D5 · Duas entradas (XML colado ou arquivo)

**Por que aceitar as duas formas?**

| Opção | Quando usar |
|-------|-------------|
| **XML colado** | Demonstração, teste rápido |
| **Caminho de arquivo** | Uso real, com o Lattes salvo |

**Decisão:** aceitar **as duas**, porque servem a propósitos diferentes. Colar é prático
para mostrar funcionando; arquivo é prático para usar no dia‑a‑dia. O servidor decide qual
foi usado no momento da chamada — o resto do código só vê o **resultado** (o LattesDocument).

---

## D6 · stdio em vez de HTTP

**Por que não uma API web?** Porque não precisamos de rede.

| Opção | Vantagem | Desvantagem |
|-------|----------|-------------|
| **HTTP (servidor web)** | Acessível por rede | Precisa de servidor, porta, pode expor dados |
| **stdio (escolhida)** | Local, rápido, seguro | Só funciona para clientes locais |

**Decisão:** **stdio** (comunicação local). O sistema não precisa ser acessível pela rede
— e isso **protege os dados** do currículo (nunca saem da máquina).

---

## D7 · SDGTaxonomy como fonte única de ODS

**Por que os ODS ficam num só arquivo?**

| Opção | Vantagem | Desvantagem |
|-------|----------|-------------|
| **ODS espalhados** por todo o código | Fácil de "escrever" de novo | Duplicado, fácil de esquecer de atualizar |
| **Fonte única (escolhida)** | Um ODS novo muda só aqui | Precisa saber onde mexer |

**Decisão:** os 17 ODS vivem em **um único arquivo** (`sds.py`). Se a ONU adicionar um 18º
objetivo, a mudança acontece aqui — e só aqui. As outras camadas não sabem *quais* ODS
existem; elas só perguntam à taxonomia.

---

## D8 · Sem banco de dados

**Por que não um banco?** Porque o sistema é **estado‑less**: ele lê o currículo, analisa,
responde — e não guarda nada entre as chamadas.

| Opção | Vantagem | Desvantagem |
|-------|----------|-------------|
| **Banco de dados** | Salva histórico | Complexidade, dados em repouso |
| **Sem banco (escolhida)** | Simples, privado, rápido | Não há histórico entre chamadas |

**Decisão:** **sem banco**. Analisar um currículo não precisa "lembrar" de chamadas
anteriores. Isso reduz complexidade e, de novo, **protege os dados** (não há nada para
vazar).

---

## 9. O fio condutor

Todas as decisões seguem **três princípios**:

1. **Verificável > inteligente** (D2, D4)
2. **Privado > acessível** (D1, D6, D8)
3. **Isolado > monolítico** (D3, D7)

Esses princípios guiam as próximas escolhas — e este documento vai crescer conforme o
sistema amadurecer.
