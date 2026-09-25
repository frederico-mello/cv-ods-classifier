# 09 · Glossário

> As palavras técnicas do projeto, explicadas como se você estivesse do meu lado.

Este é o dicionário do pacote. Se você leu um documento e travou em uma palavra,
volte aqui. Não precisa entender nada de TI para usar este glossário.

---

## O assunto, em três palavras

| Palavra | O que significa, em uma frase |
|---------|-------------------------------|
| **ODS** | Um dos 17 objetivos mundiais da ONU (problemas a resolver até 2030) |
| **Lattes** | O currículo oficial dos pesquisadores brasileiros |
| **MCP** | A "língua" que o servidor usa para falar com uma IA |

---

## Glossário completo

### ODS
Sigla de **Objetivos de Desenvimento Sustentável**. São 17 objetivos que os países da ONU
combinaram de resolver até 2030 — como erradar a pobreza, combater a mudança do clima e
garantir educação de qualidade. No nosso sistema, cada ODS vale uma nota de 0 a 100.

> **Analogia:** imagine 17 metas que o mundo inteiro se comprometeu a cumprir. O sistema
> só **avalia** o quanto o seu trabalho contribui para cada uma delas.

### Lattes
É o **currículo oficial** dos pesquisadores do Brasil, feito pela CAPES. Todo professor,
pesquisador e estudante de mestrado/doutorado tem um. Ele é um arquivo especial (um XML)
que lista formação, publicações, projetos, etc.

> **Analogia:** é como o seu currículo, mas num formato padrão que todo mundo no Brasil
> reconhece. O nosso sistema lê esse arquivo e o transforma em dados.

### MCP (Model Context Protocol)
É o **"protocolo"** — ou seja, o **conjunto de regras** — que permite um programa (o
servidor) conversar com outro (uma IA, como o goose). É como o USB é para cabos: um
padrão que todo mundo usa para conectar coisas.

> **Analogia:** o MCP é o "tomada elétrica" das IAs. O servidor pluga nessa tomada e o
> cliente (a IA) pode apertar os "botões" dele (as ferramentas).

### Servidor (MCP)
É o programa que **faz o trabalho** e fica esperando ordens. Ele não tem tela — só
responde quando alguém **chama uma ferramenta**.

> **Analogia:** é como um garçom silencioso. Ele não traz nada sozinho; só age quando
> você pede (chama uma ferramenta).

### Ferramenta
É o **botão** que o cliente aperta. O servidor expõe duas: `analyze_cv` (analisar o
currículo) e `get_sdg_report` (dar o relatório completo).

### XML
É o **formato do arquivo** do Lattes — uma forma de guardar texto com "etiquetas" que
dizem o que cada parte é. Exemplo: `<titulo>Aquecimento Global</titulo>` diz que aquele
texto é um título.

> **Analogia:** é como uma caixa de sapatos com etiquetas. A etiqueta diz "isto é um
> título", "isto é uma publicação" — e o sistema lê as etiquetas para entender o que é
> cada coisa.

### Parsear (ou "parser")
É a **ação de transformar** um arquivo (o XML bruto) em algo que o programa possa usar
(como uma lista organizada de campos). O "parser" é o **quem faz** essa transformação.

> **Analogia:** é como um moedor de carne. Entra o XML bruto (a carne), sai campo
> organizado (a carne moída) — pronto para o resto processar.

### Campo
É **cada pedaço** do currículo que o sistema extrai: uma publicação, uma formação, um
projeto. Cada campo tem três coisas: **onde** está (seção), **o que** diz (texto) e
**quanta relevância** vale (peso).

### ODS Score (nota)
É a **nota de 0 a 100** que cada ODS ganha. Não é "atende ou não" — é *"o quanto"* o
currículo contribui para aquele objetivo.

### Pista
É **a prova** de que um ODS foi alcançado. Quando o sistema acha a palavra "clima" num
campo, ele anota uma *pista*. As pistas formam a nota — e respondem à pergunta *"por que
essa nota?"*.

> **Analogia:** é como uma evidência num processo. A nota é a decisão; as pistas são os
> documentos que provam essa decisão.

### Taxonomia
É a **lista organizada** das coisas — no nosso caso, a lista dos 17 ODS com suas
palavras‑chave. É a "fonte de verdade" sobre ODS.

### Scorer (ou "motor de pontuação")
É a **peça** do sistema que **calcula** a nota. Ele pega os campos do currículo, procura
pistas e aplica a fórmula.

### Curva de saturação
É a **fórmula matemática** que transforma a soma das pistas numa nota de 0 a 100. Ela
faz a nota subir rápido no começo e desacelerar no fim (para repetir palavras não infla
a nota).

### Peso
É o **quanto cada seção vale**. Uma publicação sobre clima vale mais que uma menção solta.
O peso diz isso: publicação = 1.0, menção = 0.3.

### stdio
É a **forma** pela qual o servidor fala com o cliente — por **comunicação local**, sem
internet. É o padrão dos servidores locais.

### JSON‑RPC
É a **língua** (o formato de mensagem) que o servidor e o cliente usam. É como um
"correspondente" estruturado: o cliente manda uma ordem, o servidor responde com um
JSON.

### JSON
É o **formato da resposta** — uma forma de o servidor entregar o resultado que a IA
consegue ler facilmente.

### Cliente (de IA)
É o **programa** que usa o servidor — o goose, o Claude, etc. Ele é quem **aperta os
botões** (chama as ferramentas) e mostra o resultado ao humano.

### Determinismo
É a **garantia** de que a mesma entrada gera a mesma saída. O nosso sistema é determinístico
porque usa regras, não IA adivinhando.

### Explicabilidade
É o **quanto dá pra entender** o sistema. O nosso é explicável: toda nota vem com suas
pistas, então dá pra ver *por que* a nota é aquela.

### Privacidade
É a **proteção dos dados**. O nosso sistema não envia o currículo para a internet — tudo
roda na máquina do usuário.
