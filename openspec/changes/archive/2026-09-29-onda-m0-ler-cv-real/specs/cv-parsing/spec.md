# Spec Delta

## Purpose

Define a leitura segura e compatível das exportações XML oficiais do Currículo Lattes, produzindo campos acadêmicos rastreáveis sem expor dados pessoais.

## ADDED Requirements

### Requirement: Decodificação e leitura do XML oficial
O sistema SHALL aceitar bytes de uma exportação XML do Lattes em ISO-8859-1 ou UTF-8 e extrair conteúdo de atributos de tags oficiais em maiúsculas com hífen. O mapeamento SHALL associar elemento e atributo à seção e ao peso apropriados; atributos não mapeados só poderão ser extraídos quando seus nomes corresponderem aos padrões `TITULO-*`, `NOME-DA-*`, `DESCRICAO-*` ou `*PALAVRA-CHAVE*`, com peso 0,5. Atributos sem mapeamento ou padrão reconhecido SHALL ser ignorados. Títulos de artigo, trabalho e livro SHALL ser classificados nas seções de título/obra aplicáveis com peso 1,0.

#### Scenario: Leitura de atributos em ISO-8859-1
- **WHEN** a entrada contém tags oficiais com atributos acadêmicos e bytes ISO-8859-1
- **THEN** o sistema decodifica os valores corretamente e os inclui nos campos da seção e peso correspondentes

#### Scenario: Leitura de entrada UTF-8
- **WHEN** a entrada contém conteúdo acentuado codificado em UTF-8 válido
- **THEN** o sistema preserva os caracteres acentuados ao extrair os campos

#### Scenario: Mapeamento de título de publicação
- **WHEN** um atributo `TITULO-DO-ARTIGO`, `TITULO-DO-TRABALHO` ou `TITULO-DO-LIVRO` aparece no contexto oficial correspondente
- **THEN** seu conteúdo é extraído na seção de título ou obra aplicável com peso 1,0

#### Scenario: Atributo sem correspondência
- **WHEN** um atributo não consta do mapeamento nem corresponde a um dos padrões de segurança reconhecidos
- **THEN** seu conteúdo não é incluído como campo

### Requirement: Exclusão de dados pessoais
O sistema SHALL descartar dados pessoais durante a extração, antes de criar campos, incluindo identificadores, contato, endereço, data de nascimento, nomes próprios e nomes de autores. Valores vazios ou compostos apenas por espaços SHALL ser ignorados.

#### Scenario: Atributo pessoal negado antes do mapeamento
- **WHEN** um atributo pessoal corresponde também a um padrão de extração genérico
- **THEN** o sistema não cria campo para esse atributo

#### Scenario: Valor vazio
- **WHEN** um atributo acadêmico contém apenas espaços ou está vazio
- **THEN** o sistema não cria campo para esse valor

### Requirement: Rastreabilidade e compatibilidade do documento
Cada campo extraído SHALL identificar a tag de origem. A operação de leitura SHALL continuar fornecendo um documento Lattes utilizável pelo classificador e consumidores existentes, sem alterar a porta de entrada pública.

#### Scenario: Campo com origem
- **WHEN** um valor acadêmico é extraído de uma tag oficial
- **THEN** o campo resultante inclui o nome local da tag de origem

#### Scenario: Contrato de leitura preservado
- **WHEN** um consumidor solicita a leitura de um XML do Lattes
- **THEN** recebe o documento Lattes no contrato público existente, com os campos extraídos e sua origem
