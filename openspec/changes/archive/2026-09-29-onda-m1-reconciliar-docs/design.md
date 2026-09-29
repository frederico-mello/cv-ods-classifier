# Design

## Context

Ver `proposal.md` — Why. `lattes_sdg/scorer.py` define `SATURATION_K = 1.4`, `DECAY = 0.55`, `MAX_EVIDENCE_PER_SDG = 6` e 24 entradas em `SECTION_WEIGHTS`. `_raw_score` multiplica o peso da ocorrência de índice `i` por `DECAY ** i`; `_normalize` calcula `round(100 * (1 - exp(-raw / SATURATION_K)), 1)`. Os docs 03 e 04 contêm descrições e exemplos que precisam ser alinhados. Não há mudança de requisitos; `.openspec.yaml` usa `skip_specs: true`.

## Goals / Non-Goals

**Goals:**

- Tornar os documentos coerentes com os valores executados, preservando as chaves exatas do scorer.
- Fazer o exemplo numérico do documento 04 reproduzível pela execução das funções privadas reais do scorer.
- Corrigir o comentário de `DECAY`, sem tocar em comportamento ou testes.

**Non-Goals:**

- Alterar algoritmo, valores executáveis, testes ou contratos.
- Tratar D9 (origem das pistas) ou D10 (modo ML).

## Decisions

1. **Código como autoridade; documentação como espelho.** Copiar os valores e chaves de `lattes_sdg/scorer.py`; não inferir nem recalibrar. Alternativa rejeitada: alterar o scorer para preservar exemplos/documentação antigos, pois isso mudaria comportamento fora do escopo.
2. **Tabela íntegra no documento 03.** Publicar as 24 chaves de `SECTION_WEIGHTS` exatamente como no código, ordenadas por peso decrescente, inclusive empates. Acrescentar nota explícita de fonte da verdade no código. Alternativa rejeitada: resumo de categorias, que omite distinções e dificulta conferência.
3. **Exemplo executado, não derivado manualmente.** Explicitar os primeiros multiplicadores geométricos (`1`, `0.55`, `0.3025`), identificando-os como `DECAY ** i` aplicado por `_raw_score`. Obter bruto e normalizado chamando `_raw_score` e `_normalize` de uma instância `Scorer`, e registrar no documento o comando Python reproduzível e as entradas utilizadas. Resultado observado para `counts=[1.0, 1.0, 0.7]`: bruto `1.7617500000000001`, normalizado `71.6`. Alternativa rejeitada: calcular à mão ou manter o exemplo antigo, porque ambos podem divergir da implementação.
4. **Sem delta de capability.** Marcar `skip_specs: true`; nenhum requisito de comportamento muda. D9 e D10 permanecem fora do escopo.

## Risks / Trade-offs

- **[Risco] Uma futura alteração do código pode tornar os números documentados obsoletos.** → A nota de fonte da verdade e o comando de reprodução tornam a divergência verificável; a documentação continua sendo uma fotografia da implementação atual.
- **[Risco] A ordem entre pesos empatados poderia variar se a tabela fosse reordenada.** → Usar ordem decrescente de peso e declarar entradas com grafia idêntica à constante; preservar a ordem observada do código dentro dos empates.
- **[Risco] O resultado em ponto flutuante pode parecer impreciso.** → Mostrar o valor bruto produzido pela execução, sem arredondá-lo manualmente; a nota normalizada é o valor efetivamente devolvido pelo método.

## Migration Plan

Sem migração ou rollback de runtime: revisar e mesclar alterações exclusivamente documentais e de comentário. Reverter apenas essas edições se necessário; nenhum valor ou teste executável muda.
