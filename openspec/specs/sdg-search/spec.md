# sdg-search Specification

## Purpose
Estabelece correspondência confiável entre conteúdo acadêmico extraído e pistas dos Objetivos de Desenvolvimento Sustentável, evitando resultados por substrings acidentais.

## Requirements

### Requirement: Normalização simétrica de texto e pistas
O sistema SHALL comparar texto e pistas após a mesma normalização de minúsculas, remoção de acentos e colapso de espaços. A busca SHALL considerar uma pista correspondente apenas quando seus limites forem fronteiras de palavra, tratando caracteres não alfanuméricos, inclusive hífen, como fronteiras.

#### Scenario: Correspondência sem distinção de acentos e caixa
- **WHEN** uma pista e o texto de um campo diferem apenas por acentos ou caixa
- **THEN** a busca identifica a correspondência

#### Scenario: Não correspondência por substring
- **WHEN** a sequência de letras de uma pista aparece somente como parte de uma palavra maior
- **THEN** a busca não identifica correspondência

#### Scenario: Pista junto a hífen
- **WHEN** uma pista completa aparece como componente de uma expressão separada por hífen
- **THEN** a busca identifica a correspondência no limite do componente

### Requirement: Pistas curtas e exceções explícitas
Pistas com menos de quatro letras após normalização SHALL ser ignoradas, salvo quando a taxonomia marcar explicitamente a pista como exceção. Uma exceção SHALL ser correspondida como palavra inteira, obedecendo à regra de fronteira.

#### Scenario: Pista curta sem exceção
- **WHEN** uma pista tem menos de quatro letras normalizadas e não está explicitamente autorizada
- **THEN** ela não pontua, mesmo quando aparece como palavra isolada no texto

#### Scenario: Pista curta autorizada
- **WHEN** uma pista curta, como `CO2`, está explicitamente autorizada na taxonomia e aparece como palavra inteira
- **THEN** a busca identifica a correspondência

#### Scenario: Exceção não remove fronteira
- **WHEN** uma pista curta autorizada aparece apenas dentro de uma palavra maior
- **THEN** a busca não identifica correspondência

### Requirement: Busca ampla de temas como fallback por ODS
O sistema SHALL realizar a busca ampla por temas uma única vez para cada ODS, somente se nenhuma palavra-chave daquele ODS tiver correspondido em qualquer campo do currículo. Esse fallback SHALL produzir no máximo uma evidência de busca ampla para o ODS.

#### Scenario: Fallback quando não há palavra-chave
- **WHEN** nenhum campo do currículo corresponde a palavras-chave de um ODS
- **THEN** o sistema tenta a busca ampla uma vez para esse ODS e registra no máximo um resultado

#### Scenario: Palavra-chave impede fallback
- **WHEN** ao menos uma palavra-chave corresponde em qualquer campo de um ODS
- **THEN** o sistema não executa a busca ampla para esse ODS
