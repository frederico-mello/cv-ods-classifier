# Proposal

## Why

Os documentos 03 e 04 e o comentário do scorer descrevem pesos e parâmetros que divergem dos valores executados pelo código, reduzindo a confiabilidade da explicação e da reprodução da classificação. Esta mudança alinha somente a documentação à implementação vigente; o código é a fonte da verdade.

## What Changes

- Atualizar `docs/03-modelo-de-dados.md` com a tabela completa de `SECTION_WEIGHTS` (24 chaves idênticas ao código, em ordem decrescente de peso), além dos parâmetros `SATURATION_K = 1.4`, `DECAY = 0.55`, `MAX_EVIDENCE_PER_SDG = 6` e nota explícita de que o código é a fonte da verdade.
- Atualizar `docs/04-algoritmo.md` para refletir a fórmula e os parâmetros reais, explicitar a sequência geométrica de decaimento `1`, `0.55`, `0.3025` e sua procedência, e substituir o exemplo por valores obtidos executando `_raw_score` e `_normalize` de uma instância `Scorer`, registrando no próprio documento o comando de reprodução.
- Corrigir o comentário da linha 61 de `lattes_sdg/scorer.py` para descrever o `DECAY = 0.55` executado.
- Não alterar lógica executável nem testes.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

Nenhuma; não há mudança de comportamento nem de requisitos de capability. A change declara `skip_specs: true`.

## Impact

Somente os documentos `docs/03-modelo-de-dados.md`, `docs/04-algoritmo.md` e o comentário junto a `DECAY` em `lattes_sdg/scorer.py`. Sem alterações de API, dependências, comportamento executável ou testes.