# Spec Delta

## Purpose

Define evidências concisas e rastreáveis que expliquem a contribuição de campos curriculares para cada ODS, sem duplicações artificiais e com saída estável.

## ADDED Requirements

### Requirement: Evidências agrupadas por campo e ODS
O sistema SHALL produzir no máximo uma evidência para cada combinação de campo e ODS. Quando várias palavras-chave do mesmo ODS corresponderem ao mesmo campo, SHALL agrupá-las na evidência correspondente, em vez de gerar entradas duplicadas. Cada evidência SHALL identificar a seção e a tag de origem do campo.

#### Scenario: Várias pistas no mesmo campo e ODS
- **WHEN** duas ou mais palavras-chave do mesmo ODS correspondem ao mesmo campo
- **THEN** existe uma única evidência para esse campo e ODS, contendo as palavras-chave correspondentes agrupadas

#### Scenario: Campos distintos no mesmo ODS
- **WHEN** palavras-chave do mesmo ODS correspondem a campos distintos
- **THEN** cada campo pode ter sua própria evidência, cada uma com seção e tag de origem correspondentes

### Requirement: Limite de evidência para busca ampla
O resultado SHALL conter no máximo uma evidência de busca ampla por ODS, e somente quando nenhuma palavra-chave daquele ODS corresponder no currículo inteiro.

#### Scenario: Um único resultado de busca ampla
- **WHEN** a busca ampla encontra temas para um ODS sem correspondências de palavra-chave
- **THEN** o sistema emite no máximo uma evidência identificada como busca ampla para esse ODS

#### Scenario: Evidência de palavra-chave prevalece
- **WHEN** qualquer campo corresponde a uma palavra-chave do ODS
- **THEN** o resultado não contém evidência de busca ampla para esse ODS

### Requirement: Saída determinística
Para a mesma entrada e taxonomia, o sistema SHALL produzir saída serializada idêntica byte a byte entre execuções, preservando ordem estável de ODS, campos e palavras-chave.

#### Scenario: Repetição da mesma classificação
- **WHEN** o mesmo currículo é classificado repetidamente com a mesma taxonomia
- **THEN** o JSON resultante é idêntico byte a byte em todas as execuções
